"""Run the existing evaluation with one existing prompt element removed at a time."""
import argparse
import contextlib
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import statistics
import subprocess
import sys
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
    args = ap.parse_args()
    if args.repeats < 1 or args.limit < 0 or args.sleep < 0:
        ap.error("repeats must be positive; limit and sleep must be nonnegative")
    prompts = variants()
    if not args.dry_run and not os.environ.get("GEMINI_API_KEY"):
        ap.error("Set GEMINI_API_KEY in this terminal before live runs. Never put it in tracked files.")
    dest = ROOT / "eval" / "experiments" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    dest.mkdir(parents=True, exist_ok=False)
    dataset = (ROOT / "eval/test_set.csv").read_bytes()
    (dest / "test_set.csv").write_bytes(dataset)
    for filename in ["prompts.py", "feedback.py", "llm.py", "schemas.py", "tools.py", "eval/run_eval.py", "eval/run_ablation.py"]:
        target = dest / "source" / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / filename).read_bytes())
    manifest = {"created_utc": datetime.now(timezone.utc).isoformat(), "model": llm.GEN_MODEL,
        "repeats": args.repeats, "limit": args.limit, "sleep": args.sleep,
        "dry_run": args.dry_run, "retrieval": True, "temperature": 0.3,
        "dataset_sha256": hashlib.sha256(dataset).hexdigest(),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "prompts": prompts, "removed_elements": ELEMENTS,
        "limitations": "Only feedback system prompt is ablated. User prompt, schema, validation, tool lookup and short-answer rule stay fixed. Constraints and instructions also occur outside system prompt. Tone includes strong-answer guidance. Token usage/cost unavailable in current client; not estimated."}
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Experiment archive: {dest}", flush=True)
    if args.dry_run:
        return
    original = feedback.generate_json
    summaries = []
    for repeat in range(1, args.repeats + 1):
        for name, prompt in prompts.items():
            folder = dest / name / f"run_{repeat:02}"
            folder.mkdir(parents=True)
            FEEDBACK_PROMPTS["ablation"] = prompt
            def capture(system, user, **kwargs):
                record = {"system": system, "user": user}
                try:
                    result = original(system, user, **kwargs)
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
            with (folder / "console.log").open("w") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                runpy.run_path(str(ROOT / "eval/run_eval.py"), run_name="__main__")
            rows = json.loads((folder / "results.json").read_text())
            hits = sum(len(set(r["planted"]) & set(r["predicted"])) for r in rows)
            planted = sum(len(r["planted"]) for r in rows)
            predicted = sum(len(r["predicted"]) for r in rows)
            summaries.append({"variant": name, "repeat": repeat, "rows": len(rows), "hits": hits,
                "planted": planted, "flags": predicted, "recall": hits/planted if planted else None,
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
                for metric in ["recall", "precision", "flags", "parse_rate"]:
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
    feedback.generate_json = original


if __name__ == "__main__":
    main()
