# Prompt element ablation results

Status: Complete

Model: `gemini-3.5-flash-lite`. Planned repetitions: 3. Dataset frozen in this archive.

| Version | Runs | Recall: mean (min–max), SD | Recall change (pp) | Precision: mean (min–max), SD | Precision change (pp) | Flags/run | Input tokens/run | Output tokens/run |
|---|---:|---|---:|---|---:|---:|---:|---:|
| baseline | 3 | 28.6% (21.4–35.7%), SD 7.1 | +0.0 | 17.6% (13.6–21.7%), SD 4.1 | +0.0 | 22.7 | 19,529 | 4,072 |
| − persona | 3 | 21.4% (21.4–21.4%), SD 0.0 | -7.1 | 15.0% (15.0–15.0%), SD 0.0 | -2.6 | 20.0 | 19,570 | 3,695 |
| − context | 3 | 23.8% (21.4–28.6%), SD 4.1 | -4.8 | 16.1% (14.3–19.0%), SD 2.6 | -1.5 | 20.7 | 19,202 | 3,730 |
| − format | 3 | 35.7% (28.6–42.9%), SD 7.1 | +7.1 | 16.0% (12.5–18.8%), SD 3.2 | -1.6 | 31.3 | 18,512 | 5,372 |
| − evidence instruction | 3 | 23.8% (21.4–28.6%), SD 4.1 | -4.8 | 16.7% (15.0–20.0%), SD 2.9 | -0.9 | 20.0 | 18,832 | 3,630 |
| − constraints | 3 | 28.6% (21.4–35.7%), SD 7.1 | +0.0 | 16.9% (12.5–20.8%), SD 4.2 | -0.7 | 23.7 | 19,052 | 4,120 |
| − tone | 3 | 21.4% (21.4–21.4%), SD 0.0 | -7.1 | 13.9% (13.6–14.3%), SD 0.4 | -3.7 | 21.7 | 19,236 | 3,952 |

Change columns show the difference from the baseline mean in percentage points (pp); positive values mean an increase. Recall and precision are computed within each run, then summarized across repetitions. SD is the sample standard deviation; undefined for a single repetition. Output tokens include thinking tokens where reported. Input/output totals include the rubric tool-selection call. Token totals include recorded attempts used to repair failed rows; retries can add overhead. Usage is available only for responses returned by the provider. No monetary cost estimate is inferred from free-tier usage.

API errors across completed runs: 0.

## Interpretation limits

Only feedback system prompt is ablated. User prompt, schema, validation, tool lookup and short-answer rule stay fixed. Constraints and instructions also occur outside system prompt. Tone includes strong-answer guidance. Provider responses and usage metadata archived. Output token totals include thoughts where reported. Monetary cost is not estimated; configured account is free tier.

The test set contains 20 answers and 14 planted tags. Two short answers use deterministic rules and do not exercise prompt changes. Human-written labels are the reference; a false positive here can also reflect incomplete reference labels. These results evaluate tag agreement, not the full usefulness of feedback.

## Saved evidence

- manifest.json: exact prompts, removed elements, settings, dataset hash and commit
- source/: source snapshots; test_set.csv: frozen evaluation inputs
- each variant/run_XX/: results.json, console.log, model_calls.jsonl, provider_calls.jsonl
- runs.csv: per-run metrics; comparison.csv: aggregate statistics
