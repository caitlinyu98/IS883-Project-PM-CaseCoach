# Implementation and remaining evidence

The working branch now has a v3 pipeline: a shared per-question relevance assessment,
then none/tool/embedding selection, then common structured feedback. Both retrieval
methods supply one rubric. Tool parameters are validated; embedding candidates are
restricted to the taxonomy. The relevant features from the supplied branch were
integrated rather than overwriting main with its older schema and API client.

Updated November 14, 2026: off-topic-only transcripts receive 1/10. Mixed transcripts retain
all answers for grading, with an equal-question ceiling for unresolved nonanswers (see README). Partial relevance prompts clarification.
The relevance decision is model-based, not a deterministic guarantee. Empty/tiny reports
are rule-based and scored 1/10. Invalid numeric claims, abuse, and prompt injection are addressed
in instructions and draft tests; effectiveness requires live evaluation and human review.

The legacy app conversation request counter is labeled as practice request units, not
actual provider calls; it is not a billing cap. The limit is per interview; Start over resets the counter. Actual
provider measurements come from context-local telemetry in evaluation. Telemetry omits
credentials, prompt text, and exception messages; saved evaluation outputs contain the
submitted test transcripts and require privacy review before sharing.

Evaluation data now contains explicit question text, avoiding silent question-ID remapping.
Legacy CSV and v1/v2 prompt definitions remain for history, but this new controlled pipeline
supports v3 and v4. V4 changes only the final-feedback system prompt; v3 remains the app default. New draft test cases require review. Freeze hashes and source snapshots support
reproducibility. A final comparison needs at least five repetitions; the separate coverage
preflight reports missing required categories but does not pretend that reviewer sign-off
proves real-user provenance. No live model results were fabricated or reused from old runs.

Usage is captured before response parsing, including formatting retries and failed requests
with unknown usage. Embedding usage availability varies by provider response. Missing usage
or unverified price prevents a complete cost claim. Prices and economic assumptions are
intentionally unfilled. Indexing is in memory and reset once per repetition; no persistent
vector database is introduced. Report latencies include cold starts, which are identifiable
in call stages. Request timing excludes deliberate between-case sleep and human response time.

Full-interview runs replay fixed human-reviewed answers against generated follow-ups; they
must be checked for question/reply fit before interpreting their costs as representative.
The economic projection is gated on those checks. This is not a live-user timing study.
No automatic resumption/repair merges failures into successful runs. Interrupted files remain
available for audit; repeat affected work in a new named run and disclose it.

See TEAM_ACTION_GUIDE.md for the ordered human tasks, commands, and presentation/report formats.


## Taxonomy expansion recorded November 14, 2026

Before the corrected evaluation, the allowed weakness taxonomy expanded from seven to ten
by adding `no_business_impact`, `vague_solution`, and `unstructured`. Weakness-tag recall
remains the primary workshop metric; its label coverage has expanded. Historical seven-tag
scores are not directly comparable to ten-tag scores as evidence of improvement.

The five question-type rubrics are unchanged and remain excluded from weakness selection.
Both retrieval methods still select one weakness rubric, now from ten candidates. The
existing embedding index construction is unchanged. Review all existing expected labels
for the newly supported weaknesses, and independently review the three new AI-drafted
cases in development.json before freezing. The draft labels are proposals, not completed
human assessments. Apply each weakness only when relevant to the specific question.

November 14, 2026: the evaluator supports interleaved v3/v4 experiments and snapshots exact prompts. Report and review keys include version. See team guide section 10.
