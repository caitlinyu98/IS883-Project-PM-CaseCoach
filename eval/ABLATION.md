# Prompt ablation experiments

Run `.venv/bin/python eval/run_ablation.py` with GEMINI_API_KEY available in the terminal. Default: three repetitions of baseline plus six single-element removals, using all 20 rows (420 row evaluations; short answers use the existing deterministic rule). Use `--dry-run` to archive the plan without API calls.

Each timestamped archive contains exact prompts, removed text, dataset snapshot and hash, source snapshots, model settings, full reports, metadata, feedback request/parsed-response records, console logs, per-run metrics and comparison.csv (mean, min, max and sample standard deviation). Each run uses a new output path. API errors stop the batch after saving that run. No key is stored.

This tests only the existing feedback system prompt. User instructions, output schema, validation, rubric lookup and short-answer handling remain fixed. Some instructions are repeated in those layers; removing the format instruction does not disable the schema. The tone removal also removes the strong-answer guidance. There is no exemplar in the original prompt. An example-free data ablation is excluded because removing the answer changes the evaluation task. Precision is undefined when no tags are predicted. Raw provider responses and token usage are archived, including rubric calls and retries. Output token totals include thought tokens where reported. Monetary cost is not estimated; the configured account uses the free tier. Calls are paced at least five seconds apart, and temporary quota errors are retried up to three times with 55-second waits.

Do not interpret a dry-run archive as measured results. Live runs require sending test questions and answer texts to Gemini, as the existing evaluator does. Author and labeler columns are not included in model requests.


## Resume after a quota reset

With GEMINI_API_KEY available, run:

```sh
.venv/bin/python eval/run_ablation.py --resume eval/experiments/20261109T210131.094170Z
.venv/bin/python eval/summarize_ablation.py eval/experiments/20261109T210131.094170Z
```

Completed runs are skipped. Interrupted attempts are renamed and retained before their run is retried. Frozen prompts, model and application source are checked before resuming. New runs also checkpoint complete row reports to results.json.jsonl. Daily quota errors stop immediately. The original failed pilot and dry-run plans are separate archives and are not included in the active comparison.

The current archive is complete: 21 runs, three repetitions of seven variants, 420 answer evaluations. All final rows parsed successfully. Earlier quota, overload and connection failures remain in interrupted-attempt folders and provider logs; failed rows were repaired by reusing successful answers. Temporary overload and connection errors are retried with bounded waits.
