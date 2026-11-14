# Team actions for the Session 9 deliverable

The code prepares and records an evaluation. Your team supplies reviewed expectations, realistic inputs, benefit evidence, and interpretation. Do the steps below in order. Nothing in the draft data is a claim of completed user research. The original misaligned experiment stays historical; do not add its three repetitions to corrected repetitions.

## 1 Agree on the question you will answer

Create `docs/evaluation_decisions.md` before the final runs. Record date, team members, and these decisions in ordinary sentences:

- Primary metric: weakness-tag recall, unchanged from the workshop. Precision and F1 are safeguards, not a silently substituted headline.
- Optional success target: choose it now, explain why, and say it was added after the workshop. Do not retrospectively claim it was predefined.
- Comparison: tool-selected versus embedding-selected single rubric; same v3 final prompt and model. The common relevance check is part of both methods and their cost. This is a changed pipeline, not a rerun of the old prompt ablation.
- Selected case IDs, why they expose retrieval differences, and five or ten repetitions per version. Avoid short-answer rule cases as the main comparison.
- API model, spending allowance, and who will stop a run if quota or pricing changes.

Presentation: one sentence naming recall, the comparison, and sample size. Report: a short protocol paragraph plus this file as an appendix.

## 2 Review and complete the inputs

Open `eval/datasets/development.json` in a text editor. Each case has an exact `question`, an `answer`, `expected_tags`, `category`, `expected_behavior`, `provenance`, and `reviewed_by`. The restored legacy question comes from the old CSV notes; confirm it really is the intended question. The evaluator does not look up legacy IDs in the changing app question bank.

Ask a teammate who did not write the answer to read each question-answer pair without seeing any model output. They should mark every defensible weakness, not just the planted one. Agree on disputed labels and write a short rationale in an optional `label_notes` field. Fill `reviewed_by` with a name or agreed team identifier, and fill the dataset's top-level `reviewed_by` when finished. Do not just remove the draft label without doing the review.

Ensure the final evidence contains at least 20 realistic inputs and includes empty, outside-scope, wrong-kind, abusive, malicious, invalid-value, and altered-familiar examples. Review the AI-drafted examples for realism. Include missing-prioritization and multiple-weakness examples. For an altered familiar case, record the original scenario, what fact changed, and why that should change the answer. Avoid copying copyrighted long examples.

For stronger evidence, invite classmates to answer actual case questions in their own words. Explain that answers go to the selected model provider and will be used for evaluation, obtain their agreement, and remove names and identifying details. Record `provenance` accurately, such as 'classmate submission, anonymized, collected 2026-11-xx'. Do not label AI drafts as user submissions. Ask the instructor if their meaning of 'real inputs' requires collected submissions.

Keep development examples separate from a fresh held-out set. Put the latter in `eval/datasets/heldout_template.json`, saving as `heldout.json`. Have a reviewer supply the expected outcomes before running it. Do not tune prompts against held-out results and then describe the same cases as unseen.

Presentation: a small category/count table and one representative difficult input. Report: the same table, provenance, labeling procedure, disagreements, and dataset hash.

## 3 Set up Python and verify offline

From the repository root in a terminal:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python eval/run_eval.py --dataset eval/datasets/development.json
```

The last command only validates and prints the plan. It does not call Gemini. The new evaluator uses JSON datasets; `eval/test_set.csv` is retained as historical source material, not the live question-mapping mechanism.

For final reviewed data:

```sh
python eval/run_eval.py --dataset eval/datasets/heldout.json --freeze
```

This creates a SHA-256 lock. Editing the dataset changes its hash and requires a documented review and new freeze. It is an audit aid, not tamper-proof certification. Save the reviewed file and lock in Git before running. The final runner refuses unreviewed or changed datasets.

## 4 Verify prices before live runs

Edit `eval/config/prices.json`. Find each actual model in the official Gemini Developer API pricing documentation. Record the URL, date checked, USD per million input/output tokens, and applicable cached-input rate. Confirm whether candidate tokens and thinking tokens are separate in usage metadata and how each is billed. The config's `output_includes_thoughts` means 'add the separately reported thought count to billable output'; do not double-count if your SDK/provider defines fields differently.

For embeddings, verify the input-token field actually present in the response and set `input_field` accordingly. If the response lacks token usage, keep that cost unknown and obtain provider-supported usage evidence. Do not estimate characters and call it measured tokens. No separate vector database is needed by this implementation.

Do a small development smoke run before the full comparison. Supply your key locally through the environment or Streamlit secrets. Do not paste it into a tracked file, presentation, or report. `--run` is the explicit switch that makes API calls. The configured default model must be available to your project; choose a verified model with `--model` if needed. The harness disables cross-model fallback.

```sh
python eval/run_eval.py --dataset eval/datasets/development.json --ids human_01 human_02 --modes tool embedding --repeats 1 --run
```

Inspect saved transcripts, call stages, and usage in the newly printed `eval/runs/<run-id>` folder. Check that all transmitted questions match their answers and that usage categories can be priced. Unknown fields are not zero. Set a provider-side quota/budget where available; the harness prints attempted reports, not a guaranteed dollar cap.

## 5 Run the final comparison and remaining cases

Use your documented subset of IDs, or omit `--ids` for all cases:

```sh
python eval/run_eval.py --dataset eval/datasets/heldout.json --final --modes tool embedding --repeats 5 --ids CASE_ID_1 CASE_ID_2 --run
```

Replace the example IDs with actual ones. For cases outside the comparison, run the chosen mode once, also from frozen data. You may include `none` as a third baseline if budget permits. Randomized order is reproducible from the seed. Each repetition rebuilds the in-memory embedding index once; cold starts are logged separately. Index rebuilding represents this implementation, not a persistent production cache.

Every run creates a new folder. Save its path in your decisions file. Do not overwrite failed cases with repaired successes. If interrupted, keep the partial folder and run a separately identified repetition; report the interruption. The code does not automatically resume or merge runs. An incomplete repetition cannot be called a completed final comparison.

Generate its report:

```sh
python eval/report.py eval/runs/REPLACE_WITH_RUN_ID
```

Read `comparison.csv` for per-repetition metrics and observed token subtotals, `cost_ledger.csv` for request-level arithmetic, and `session09_report.md` for the draft written report. Raw results include answers: keep them private until you have reviewed them for identifiers and participant permission. They are ignored by Git by default.

Presentation: one table with recall mean/range, precision, input/output/thought tokens, dollars, and latency for each method. State the number of unique cases and repetitions separately. Report: add configuration, selected IDs, source hashes, failure rates, and caveats about the small sample.

## 6 Judge behavior and identify a metric-blind failure

Open the generated `human_review.csv` in Excel or a text editor. For each saved output, enter a reviewer, `yes` or `no` in `behavior_pass`, `evidence_supported`, and `fix_actionable`, and explain any failure. Judge the expected behavior written before the run. The code cannot verify whether a suggestion is actually helpful merely because JSON is valid.

Find one real output that correctly identifies all expected tags (recall passes) but invents evidence, gives a bad fix, misses an invalid number, or otherwise fails. Copy the exact defective sentence into `metric_blind_failure_quote`; explain why it is wrong and propose a check. Do not write a hypothetical output as if observed. If none appears, try targeted development cases and disclose that selection. Label the new cases before running them.

For method disagreements, inspect `meta.retrieved_tags` and tool calls. Explain whether the selected rubric supports the difference. Use the changed-facts case to investigate responsiveness to facts. Do not claim to know hidden reasoning or training-data provenance.

Presentation: one input/output snippet showing 'recall pass, coaching failure' and the extra check. Report: exact case ID, run/mode/repetition, expected and predicted tags, quotation, and review rationale. Rerun report generation after completing review fields.

## 7 Measure complete interviews separately

Review `eval/datasets/sessions_draft.json`. The draft combines four team-authored answers and deliberately leaves follow-up replies blank. Create several representative four-question transcripts with short, typical, and long substantive answers and follow-up answers. Independently label the complete session, including gaps repaired in follow-ups. Use `unit: full_interview`, review, and freeze the file.

The harness generates real follow-up questions but uses your prerecorded follow-up answers. After each run, read every generated question and the supplied reply together. Mark `session_followup_fit` as `yes` only if they match. If not, the replay is not a valid session-cost sample: create a corrected/new session, document it, and run it. Do not merely mark mismatches as acceptable. This is a replay benchmark, not a timed live-user study.

Run sessions with the same command and modes, pointing to the session dataset. Generate a report and fill the review sheet. Projection stays pending until every session reply fit is reviewed and prices and assumptions are complete. Use the cost of all necessary calls, including relevance, follow-ups, tool selection/query embeddings, feedback, and retries. Report cost per attempted and completed session and explain failures. Request latency excludes human typing time; do not call it total time spent practicing.

Presentation: measured dollars per full interview plus its token arithmetic. Report: workload composition, cold/warm costs, missing usage, and limits of fixed-reply replay.

## 8 Measure the benefit and record assumptions

Create `docs/benefit_study.csv` with columns: participant_id, task_id, method, minutes, review_correction_minutes, useful_feedback_rating, reviewer, notes. Do not include names. Recruit a small group, for example 6–10 classmates, and describe it as exploratory. Compare CaseCoach with the method they actually use. Give comparable tasks and alternate which method people use first. Have another person judge feedback usefulness without knowing which method produced it where practical.

Net time saved is comparison-method time minus app-method time including checking/correction, at comparable quality. Practice taking longer can still be beneficial; do not force a time-saving claim if the evidence does not support it. Alternatively, argue the social value of access to practice and measure usefulness/access rather than invented financial returns.

Edit `eval/config/assumptions.json`: population served, sessions per student per year, hosting, storage, other paid services, maintenance hours/rate, build hours/rate, net minutes saved, hourly time value, annual index rebuilds, and measured cost per index build. Put a source or explicit planning rationale beside every value. Use zero only where justified. Include taxes or other charges if material to the selected plan. Choose a realistic adoption scenario, not a population you merely hope to reach. Student time value is not cash revenue. Do not count both saved time and displaced coaching spend for the same benefit without justification.

Run the report generator on the reviewed full-session run. It computes ongoing and first-year costs, break-even volume, ROI, and half/base/double time-saving scenarios when inputs are complete. Break-even assumes fixed costs stay fixed over that range. If adoption is more uncertain, also halve/double users with separate assumption files. Explicitly state if the conclusion flips.

Presentation: one annual-cost calculation, one benefit/break-even figure, and a three-row sensitivity table. Report: full assumptions table with measured versus assumed labels, sources, arithmetic, limitations, and social-value argument if appropriate.

## 9 Assemble and check the final deliverable

Use this presentation sequence: (1) user problem and unchanged primary metric; (2) test categories and deterministic checks; (3) repeated technique comparison with tokens and costs; (4) why the methods differed and one metric-blind failure; (5) measured session cost and annual volume; (6) benefit, break-even, sensitivity, and assumptions; (7) build versus buy and limitations.

For the written report, start with a short conclusion supported by the new evidence. Then include the five testing requirements, followed by the six numbered cost sections already generated in `session09_report.md`. Replace pending interpretation text with your reviewed findings. Put raw tables, manifests, and evidence IDs in an appendix, rather than crowding the presentation. Use the report's build-versus-buy paragraph, adapted to your actual workload and maintenance capacity.

Before submission, verify: at least 20 unique realistic reviewed cases across the evidence; all required difficult categories; five complete repetitions per comparison case/method; recall retained or change disclosed; one actual metric-blind failure; complete usage or clearly stated unknowns; full-session cost; non-API costs; benefit and break-even; sourced assumptions; half/double sensitivity; and build-versus-buy. Updated November 14, 2026: the practice counter resets per interview. All submissions remain visible and are used for grading; unresolved short or off-topic answers lower the score. Review expected results using this policy, not the earlier unscored policy. An honest negative result is a valid finding. Do not present mocked software tests as live model evaluation results.
