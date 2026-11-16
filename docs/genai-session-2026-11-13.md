# GenAI session log — 2026-11-13

Tool: Claude Code (desktop app), model Claude Fable 5.2 (`claude-fable-5-2`).
Purpose of this file: a record of what was asked and what the tool did, for the
Generative AI appendix. It contains no slide or report text.

## What was asked

1. Edit the presentation deck (Google Slides, "Investor Pitch Template").
2. Write what should go in the empty slides.
3. Produce this file, with the slide content.

## What the tool did

- Read the deck and its comments through the Google Drive connector. Made no edits.
- Ran `git fetch origin` and listed recent commits and files on `origin/main`.
- Searched `app.py` and `llm.py` on `origin/main` for the session cap and cost code.
- Declined requests 1, 2 and the second half of 3: directive §9 prohibits AI from
  writing, drafting or rewording any prose for the slides, including bullets to
  convert.
- Wrote this file. Nothing was committed or pushed.

## What the tool found (fact and grammar check of existing slide text)

- Slide 1: title says "IS833"; the course is IS883.
- Slide 3: "it requires, peers to help or paying to professional services" has a
  stray comma and "paying to".
- Slide 3: "Failing at this opportunity include an opportunity cost" has a
  subject–verb mismatch.
- The deck file is still named "Investor Pitch Template".
- Slides 5–10 are unfilled template placeholders.
- Open comment from Jacobo (Nov 3) asks Caitlin and Max to complete slide 6.
- `origin/main` includes PR #32 (model and API key switching) and PR #33
  (score-band split); the local branch `caitlin-score-top-band` is behind it.

## Ideation given (questions per slide and where the evidence is)

| Slide | Question the placeholders ask | Where to look |
|---|---|---|
| 5 — What we built | What can a student do now that they couldn't, and what does one session look like? | Run the app, take a screenshot; `app.py` |
| 6 — How it works | What goes in, what happens in the middle, what comes out? | `docs/architecture-diagram.jpg`, `llm.py`, `tools.py`, `retrieval.py`, `feedback.py` |
| 7 — Why we built it this way | Which three choices did the team debate, and what did each cost? | PRs #30, #31, #32, #33 |
| 8 — Does it work? | What did the eval measure, on what test set, against what baseline, and what does it miss? | `eval/run_eval.py`, `eval/test_set.csv` |
| 9 — What it would cost | Cost per session, the assumption behind it, and how it moves if that changes? | `MAX_REQUESTS` at `app.py:207`, model choice in `llm.py` |
| 10 — What this makes possible | What would you trust the tool with, and what not? | Failure paths in `app.py`, weak spots in the eval |

## For the appendix

Category of use: ideation and fact checking. Keep the session transcript as the
supporting evidence.
