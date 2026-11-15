"""Run the existing evaluation with one existing prompt element removed at a time."""
import argparse
import contextlib
import csv
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import feedback
import llm
from prompts import FEEDBACK_PROMPT_V1, FEEDBACK_PROMPTS

ELEMENTS = {
    "persona": "You are a strict but fair senior product manager and interview coach.\n",
    "context": "You receive an interview transcript, a list of allowed weakness tags, and rubric excerpts.\n",
    "format": 'Reply with JSON only, in this exact shape:\n{"overall_summary": "...",\n "strengths": ["..."],\n "weaknesses": [{"tag": "<one allowed tag>", "evidence": "...", "fix": "..."}],\n "next_steps": ["..."]}\n',
    "evidence_instruction": "- Report a weakness only if the candidate's answers actually show it. Evidence must point to what the candidate said or failed to say.\n- Each fix must be a concrete action the candidate can take, not general advice.\n",
    "constraints": "- Use only tags from the allowed list. Never invent a tag.\n- Keep strengths and next_steps to at most 3 items each.",
    "tone": "- Do not flatter. If the answers are strong, return an empty weaknesses list.\n",
}


def variants():
    result = {"baseline": FEEDBACK_PROMPT_V1}
    for name, fragment in ELEMENTS.items():
        # The two constraint rules are separated by other elements.
        fragments = fragment.splitlines(keepends=True) if name == "constraints" else [fragment]
        prompt = FEEDBACK_PROMPT_V1
        for part in fragments:
            assert prompt.count(part) == 1, (name, part)
            prompt = prompt.replace(part, "", 1)
        result["without_" + name] = prompt
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sleep", type=float, default=4)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", type=Path, help="Resume an archive, preserving completed runs and interrupted attempts")
    args = ap.parse_args()
    if args.repeats < 1 or args.limit < 0 or args.sleep < 0:
        ap.error("repeats must be positive; limit and sleep must be nonnegative")
    prompts = variants()
    if not args.dry_run and not os.environ.get("GEMINI_API_KEY"):
        ap.error("Set GEMINI_API_KEY in this terminal before live runs. Never put it in tracked files.")
    if args.resume:
        dest = args.resume.resolve()
        manifest = json.loads((dest / "manifest.json").read_text())
        if manifest["dry_run"]:
            ap.error("A dry-run plan is not a live experiment; start a new batch")
        if manifest["prompts"] != prompts or manifest["model"] != llm.GEN_MODEL:
            ap.error("Prompts or model changed; start a new experiment")
        for name in ["prompts.py", "feedback.py", "llm.py", "schemas.py", "tools.py", "question_bank.py", "data/questions.json", "sources/rubrics.json"]:
            if (ROOT / name).read_bytes() != (dest / "source" / name).read_bytes():
                ap.error(f"{name} changed; start a new experiment")
        if hashlib.sha256((dest / "test_set.csv").read_bytes()).hexdigest() != manifest["dataset_sha256"]:
            ap.error("Archived dataset hash mismatch")
        args.repeats, args.limit, args.sleep = manifest["repeats"], manifest["limit"], manifest["sleep"]
        if not args.dry_run:
            revision = dest / "resume_sources" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
            revision.mkdir(parents=True)
            for name in ["run_ablation.py", "run_eval.py"]:
                (revision / name).write_bytes((ROOT / "eval" / name).read_bytes())
    else:
        dest = ROOT / "eval" / "experiments" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        dest.mkdir(parents=True, exist_ok=False)
        dataset = (ROOT / "eval/test_set.csv").read_bytes()
        (dest / "test_set.csv").write_bytes(dataset)
        for filename in ["prompts.py", "feedback.py", "llm.py", "schemas.py", "tools.py", "question_bank.py", "data/questions.json", "sources/rubrics.json", "eval/run_eval.py", "eval/run_ablation.py"]:
            target = dest / "source" / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / filename).read_bytes())
        manifest = {"created_utc": datetime.now(timezone.utc).isoformat(), "model": llm.GEN_MODEL,
            "repeats": args.repeats, "limit": args.limit, "sleep": args.sleep,
            "dry_run": args.dry_run, "retrieval": True, "temperature": 0.3, "minimum_api_call_interval_seconds": 5,
            "dataset_sha256": hashlib.sha256(dataset).hexdigest(),
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "prompts": prompts, "removed_elements": ELEMENTS,
            "limitations": "Only feedback system prompt is ablated. User prompt, schema, validation, tool lookup and short-answer rule stay fixed. Constraints and instructions also occur outside system prompt. Tone includes strong-answer guidance. Provider responses and usage metadata archived. Output token totals include thoughts where reported. Monetary cost is not estimated; configured account is free tier."}
        (dest / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Experiment archive: {dest}", flush=True)
    if args.dry_run:
        return
    provider_models = llm._get_client().models
    provider_generate = provider_models.generate_content
    def audit_provider(*call_args, **kwargs):
        record = {"utc": datetime.now(timezone.utc).isoformat(), "model": kwargs.get("model")}
        started = time.monotonic()
        try:
            response = provider_generate(*call_args, **kwargs)
            record["response"] = response.model_dump(mode="json")
            return response
        except Exception as exc:
            record["error"] = str(exc)
            raise
        finally:
            record["seconds"] = time.monotonic() - started
            with (folder / "provider_calls.jsonl").open("a") as stream:
                stream.write(json.dumps(record) + "\n")
    provider_models.generate_content = audit_provider
    original = feedback.generate_json
    original_tools = feedback.generate_with_tools
    last_call = [0.0]
    def paced(fn, *call_args, **kwargs):
        for attempt in range(4):
            time.sleep(max(0, 5.0 - (time.monotonic() - last_call[0])))
            last_call[0] = time.monotonic()
            try:
                return fn(*call_args, **kwargs)
            except llm.LLMError as exc:
                if "429" in str(exc) and ("PerDay" in str(exc) or "per day" in str(exc)):
                    (dest / "status.json").write_text(json.dumps({"status": "daily_quota_exhausted", "updated_utc": datetime.now(timezone.utc).isoformat(), "error": str(exc)}, indent=2))
                    raise SystemExit("Gemini daily quota exhausted. Results are preserved; resume this archive after the quota resets.") from exc
                if not any(code in str(exc) for code in ("429", "503")) or attempt == 3:
                    raise
                # Preserve provider errors, and wait out the minute quota window.
                with (dest / "retry_errors.jsonl").open("a") as stream:
                    stream.write(json.dumps({"utc": datetime.now(timezone.utc).isoformat(), "attempt": attempt + 1, "error": str(exc)}) + "\n")
                time.sleep(55)
    def paced_tools(*call_args, **kwargs):
        return paced(original_tools, *call_args, **kwargs)
    feedback.generate_with_tools = paced_tools
    summaries = []
    if args.resume and (dest / "runs.csv").exists():
        for row in csv.DictReader((dest / "runs.csv").open()):
            for key in row:
                if key != "variant":
                    row[key] = float(row[key]) if row[key] else None
            if row["api_errors"] == 0:
                summaries.append(row)
    (dest / "status.json").write_text(json.dumps({"status": "running", "updated_utc": datetime.now(timezone.utc).isoformat()}))
    for repeat in range(1, args.repeats + 1):
        for name, prompt in prompts.items():
            folder = dest / name / f"run_{repeat:02}"
            if any(r["variant"] == name and r["repeat"] == repeat for r in summaries):
                print(f"Preserved completed {name}, repetition {repeat}", flush=True)
                continue
            previous_results = None
            if folder.exists():
                interrupted = folder.with_name(folder.name + "_interrupted_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ"))
                folder.rename(interrupted)
                if (interrupted / "results.json").exists():
                    previous_results = interrupted / "results.json"
            folder.mkdir(parents=True)
            if previous_results:
                for log_name in ("provider_calls.jsonl", "model_calls.jsonl"):
                    if (interrupted / log_name).exists():
                        shutil.copyfile(interrupted / log_name, folder / log_name)
            FEEDBACK_PROMPTS["ablation"] = prompt
            def capture(system, user, **kwargs):
                record = {"system": system, "user": user}
                try:
                    result = paced(original, system, user, **kwargs)
                    record["parsed_response"] = result
                    return result
                except Exception as exc:
                    record["error"] = str(exc)
                    raise
                finally:
                    with (folder / "model_calls.jsonl").open("a") as stream:
                        stream.write(json.dumps(record) + "\n")
            feedback.generate_json = capture
            sys.argv = ["run_eval.py", "--version", "ablation", "--csv", str(dest / "test_set.csv"),
                "--limit", str(args.limit), "--sleep", str(args.sleep), "--output", str(folder / "results.json")]
            if previous_results:
                sys.argv.extend(["--resume-results", str(previous_results)])
            with (folder / "console.log").open("w") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                runpy.run_path(str(ROOT / "eval/run_eval.py"), run_name="__main__")
            rows = json.loads((folder / "results.json").read_text())
            hits = sum(len(set(r["planted"]) & set(r["predicted"])) for r in rows)
            planted = sum(len(r["planted"]) for r in rows)
            predicted = sum(len(r["predicted"]) for r in rows)
            usage = [json.loads(line).get("response", {}).get("usage_metadata") or {}
                     for line in (folder / "provider_calls.jsonl").read_text().splitlines()]
            input_tokens = sum(u.get("prompt_token_count") or 0 for u in usage)
            output_tokens = sum((u.get("candidates_token_count") or 0) + (u.get("thoughts_token_count") or 0) for u in usage)
            summaries.append({"variant": name, "repeat": repeat, "rows": len(rows), "hits": hits,
                "planted": planted, "flags": predicted, "input_tokens": input_tokens, "output_tokens_including_thoughts": output_tokens, "recall": hits/planted if planted else None,
                "precision": hits/predicted if predicted else None,
                "parse_rate": sum(r["parse_ok"] for r in rows)/len(rows) if rows else None,
                "api_errors": sum(r["error"] is not None for r in rows)})
            with (dest / "runs.csv").open("w") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(summaries[0]))
                writer.writeheader(); writer.writerows(summaries)
            aggregate = []
            for variant in prompts:
                group = [r for r in summaries if r["variant"] == variant]
                if not group: continue
                row = {"variant": variant, "runs": len(group)}
                for metric in ["recall", "precision", "flags", "parse_rate", "input_tokens", "output_tokens_including_thoughts"]:
                    values = [r[metric] for r in group if r[metric] is not None]
                    for stat, fn in [("mean", statistics.mean), ("min", min), ("max", max), ("sd", lambda v: statistics.stdev(v) if len(v)>1 else None)]:
                        row[metric+"_"+stat] = fn(values) if values else None
                aggregate.append(row)
            with (dest / "comparison.csv").open("w") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(aggregate[0]))
                writer.writeheader(); writer.writerows(aggregate)
            print(f"Saved {name}, repetition {repeat}: {summaries[-1]}", flush=True)
            if any(r["error"] for r in rows):
                raise SystemExit("Stopped after API errors. Partial results are preserved; resolve the error before a new experiment.")
    (dest / "status.json").write_text(json.dumps({"status": "complete", "updated_utc": datetime.now(timezone.utc).isoformat()}))
    feedback.generate_json = original
    feedback.generate_with_tools = original_tools
    provider_models.generate_content = provider_generate


if __name__ == "__main__":
    main()
