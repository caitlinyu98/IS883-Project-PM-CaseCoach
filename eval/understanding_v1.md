The results do **not** show that tool calling is inherently worse. They show that, in these runs, the **no-rubric condition had the best F1**—and the recorded failures make the comparison uncertain.

I checked the saved results for all 20 test answers:

| Mode | F1 | Recall | Precision | Valid reports |
|---|---:|---:|---:|---:|
| None | **0.348** | 0.571 | 0.250 | 16/20 |
| Tool | 0.138 | 0.143 | 0.133 | 15/20 |
| Embedding | 0.258 | 0.286 | 0.235 | 13/20 |

“None” found more planted weaknesses, but also made many more false-positive predictions: **24**, compared with **13** for each other mode. Its higher recall outweighed the lower precision in the F1 score.

**429 errors could have affected this.** The saved results show invalid/failed reports for 4, 5, and 7 rows respectively, but don’t record why they failed. In `run_eval.py`, an API exception is counted as a failed row with no predicted tags, which hurts the metrics. The `parse_ok` field doesn’t distinguish an API/rate-limit failure from a response that failed parsing or validation. Check the terminal output from each run for `429 RESOURCE_EXHAUSTED`; we can’t confirm the cause from these result files alone.

It also matters that the runs were sequential: if “none” ran first, it may have had more quota available. Tool mode makes an additional Gemini call to choose a rubric, and embedding mode makes embedding calls as well as a feedback-generation call. That makes rate limits a plausible confounder.

And tool calling is not automatically more accurate: it’s just one way to select rubric evidence. In this implementation, it selects **one** weakness rubric, and embedding retrieves **one** rubric too. Neither is guaranteed to cover every planted weakness.

For a fairer comparison, rerun when quota is available, check that each mode has comparable successful-report counts, and repeat the modes in a different order. Treat these numbers as preliminary until the harness records API errors separately from parsing failures.