# Written with Claude (Anthropic) as coding assistant. Log the exchange in the GenAI appendix.
# --- Caitlin: eval harness, metric = % planted weaknesses identified (change name to the real owner) ---
# Usage (set GEMINI_API_KEY in your terminal first):
#   python eval/run_eval.py --limit 2                 # develop on 2 rows
#   python eval/run_eval.py --limit 0 --no-retrieval  # full set, retrieval off
import argparse
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from feedback import generate_report  # noqa: E402
from prompts import QUESTIONS  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--csv", default=os.path.join(os.path.dirname(__file__), "test_set.csv"))
ap.add_argument("--version", default="v1")
ap.add_argument("--no-retrieval", action="store_true")
ap.add_argument("--limit", type=int, default=2, help="0 means all rows")
ap.add_argument("--sleep", type=float, default=4.0, help="seconds between calls (free tier rate limit)")
args = ap.parse_args()

rows = list(csv.DictReader(open(args.csv, encoding="utf-8")))
if args.limit:
    rows = rows[: args.limit]

hits = planted_total = extra = predicted_total = parsed = 0
out = []
for r in rows:
    planted = {t for t in r["planted_weaknesses"].split("|") if t}
    transcript = [{"question": QUESTIONS[int(r["question_index"])], "answer": r["answer"]}]
    try:
        res = generate_report(transcript, version=args.version, use_retrieval=not args.no_retrieval)
        report = res["report"]
    except Exception as e:  # API error counts as a failed row, not a crash
        print(r["id"], "API error:", e)
        report = None
    ok = report is not None
    parsed += ok
    predicted = {w["tag"] for w in report["weaknesses"]} if ok else set()
    hits += len(planted & predicted)
    planted_total += len(planted)
    extra += len(predicted - planted)
    predicted_total += len(predicted)
    out.append({"id": r["id"], "planted": sorted(planted), "predicted": sorted(predicted), "parse_ok": ok})
    time.sleep(args.sleep)

print(f"rows: {len(rows)}  parse rate: {parsed}/{len(rows)}")
print(f"PRIMARY  % planted weaknesses identified: {hits}/{planted_total}"
      f" = {100 * hits / planted_total:.1f}%" if planted_total else "no planted weaknesses in set")
print(f"SECONDARY  precision (guards against tagging everything): {hits}/{predicted_total}"
      f" = {100 * hits / predicted_total:.1f}%" if predicted_total else "no tags predicted")
tag = f"{args.version}_{'noret' if args.no_retrieval else 'ret'}"
with open(os.path.join(os.path.dirname(__file__), f"results_{tag}.json"), "w") as f:
    json.dump(out, f, indent=2)  # ids and tags only, no answer text
