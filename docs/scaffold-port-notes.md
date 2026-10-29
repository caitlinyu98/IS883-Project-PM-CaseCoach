# Porting notes: what is left in the archived scaffold

The `starter-scaffold` branch (renamed `archive-llm-test`) was a test to get the LLM working.
Caitlin ported the structured output schema (`schemas.py`), the 60 second API timeout (`llm.py`)
and removed the debug errors from `app.py`. Two pieces are left for **Max** to build on `main`,
in his own branches, so the commits are his.

## 1. Tool calling (directives §5.1, item 2)

Reference: `tools.py` and lines 90 to 92 of `app.py` on `archive-llm-test`.

- The pattern: write a plain Python function with type hints and a docstring, pass it in
  `types.GenerateContentConfig(tools=[my_function])`, and the google-genai SDK lets the model
  decide to call it and feeds the result back automatically.
- Do NOT copy the scaffold's chat interviewer. `main` keeps its fixed four question flow.
- Open decision (plan doc): put the tool in the follow up step (model picks a weakness tag and
  calls a rubric lookup such as `lookup_rubric_by_tag(tag)` over `sources/rubrics.json`) or in
  the feedback step. Pick the place where removing the tool visibly changes the output.
- Log every call (name, argument, result id) so the demo can show where it fires.
- Each tool call is an extra API round trip: count it against the request cap.

## 2. Token logging for the cost model (directives §5.6, item 1)

Reference: lines 51 and 74 of `app.py` on `archive-llm-test` (it only logged `total_token_count`).

- In `llm.py`, after each `generate_content` and `embed_content` call, record
  `resp.usage_metadata.prompt_token_count` (input) and `resp.usage_metadata.candidates_token_count`
  (output) separately: they are priced at different rates.
- Record which step made the call (follow up, feedback, embedding, tool round trip) so the
  cost per full interview can be added up.
- `eval/run_eval.py` should save the same counts, so cost comes from the whole test set.
