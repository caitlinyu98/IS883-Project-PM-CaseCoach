"""Create a readable table from an archived ablation experiment."""
import argparse
import csv
import json
from pathlib import Path

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("experiment", type=Path)
args = ap.parse_args()
p = args.experiment
manifest = json.loads((p / "manifest.json").read_text())
rows = list(csv.DictReader((p / "comparison.csv").open()))
baseline = next(row for row in rows if row["variant"] == "baseline")
for row in rows:
    for metric in ("recall", "precision"):
        key = metric + "_mean"
        row[metric + "_change_pp"] = (float(row[key]) - float(baseline[key])) * 100 if row[key] and baseline[key] else ""
with (p / "comparison.csv").open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
runs = list(csv.DictReader((p / "runs.csv").open()))
complete = len(runs) == len(manifest["prompts"]) * manifest["repeats"]
lines = ["# Prompt element ablation results", "", "Status: " + ("Complete" if complete else "Partial — experiments still running or stopped"), "", f"Model: `{manifest['model']}`. Planned repetitions: {manifest['repeats']}. Dataset frozen in this archive.", "", "| Version | Runs | Recall: mean (min–max), SD | Recall change (pp) | Precision: mean (min–max), SD | Precision change (pp) | Flags/run | Input tokens/run | Output tokens/run |", "|---|---:|---|---:|---|---:|---:|---:|---:|"]
def pct(row, key):
    if not row[key + "_mean"]: return "undefined"
    sd = f"{float(row[key+'_sd'])*100:.1f}" if row[key+'_sd'] else "n/a"
    return f"{float(row[key+'_mean'])*100:.1f}% ({float(row[key+'_min'])*100:.1f}–{float(row[key+'_max'])*100:.1f}%), SD {sd}"
def delta(row, metric):
    value = row[metric + "_change_pp"]
    return f"{value:+.1f}" if value != "" else "undefined"
for row in rows:
    label = row["variant"].replace("without_", "− ").replace("_", " ")
    lines.append(f"| {label} | {row['runs']} | {pct(row, 'recall')} | {delta(row, 'recall')} | {pct(row, 'precision')} | {delta(row, 'precision')} | {float(row['flags_mean']):.1f} | {float(row['input_tokens_mean']):,.0f} | {float(row['output_tokens_including_thoughts_mean']):,.0f} |")
lines += ["", "Change columns show the difference from the baseline mean in percentage points (pp); positive values mean an increase. Recall and precision are computed within each run, then summarized across repetitions. SD is the sample standard deviation; undefined for a single repetition. Output tokens include thinking tokens where reported. Input/output totals include the rubric tool-selection call. Token totals include recorded attempts used to repair failed rows; retries can add overhead. Usage is available only for responses returned by the provider. No monetary cost estimate is inferred from free-tier usage.", "", "API errors across completed runs: " + str(sum(int(float(r['api_errors'])) for r in runs)) + ".", "", "## Interpretation limits", "", manifest["limitations"], "", "The test set contains 20 answers and 14 planted tags. Two short answers use deterministic rules and do not exercise prompt changes. Human-written labels are the reference; a false positive here can also reflect incomplete reference labels. These results evaluate tag agreement, not the full usefulness of feedback.", "", "## Saved evidence", "", "- manifest.json: exact prompts, removed elements, settings, dataset hash and commit", "- source/: source snapshots; test_set.csv: frozen evaluation inputs", "- each variant/run_XX/: results.json, console.log, model_calls.jsonl, provider_calls.jsonl", "- runs.csv: per-run metrics; comparison.csv: aggregate statistics", ""]
(p / "REPORT.md").write_text("\n".join(lines))
print(p / "REPORT.md")
