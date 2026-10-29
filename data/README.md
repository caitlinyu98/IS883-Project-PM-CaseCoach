# data/ — the content the app reads

**Owner: Jimena.** This folder is the app's knowledge. The code is only as good as
what is written here: the retrieval step searches these files, and the feedback
model judges answers against them. Everything here is written by our team
(directives §3.2). If you summarize an outside source, its terms must allow it,
and you list it under "Sources" at the bottom of this file.

There are three files to fill in.

---

## 1. `questions.json` — the question bank

**Goal:** 20 B2B SaaS interview questions, spread across the 5 types below
(about 4 per type), so the interviewer always has unused questions to pick from.

Each question is one entry with exactly these four fields:

| Field | What to write |
| --- | --- |
| `id` | `q01`, `q02`, ... Never reuse or renumber an id: the evaluation refers to them. |
| `type` | One of: `product_design`, `metrics`, `prioritization`, `strategy`, `behavioral`. Spelled exactly like this, because `tools.py` filters on it. |
| `question` | The question exactly as the interviewer will ask it, in English. |
| `strong_answer_includes` | A short list, separated by semicolons, of what a strong answer covers. This is what retrieval finds and what the follow-ups target. |

The file starts with 2 examples. Keep the format (square brackets around the
whole list, a comma between entries, no comma after the last one). If the app
crashes on start, a missing comma here is the usual cause: paste the file into
[jsonlint.com](https://jsonlint.com) to find it.

---

## 2. `rubrics.md` — what good and bad answers look like

Each section that starts with `## ` becomes one retrieval chunk. Write two kinds
of sections:

**A. One section per question type (5 sections).** What a strong answer to that
type of question does, in order. Example heading: `## metrics`.

**B. One section per weakness category (8 sections).** How the weakness shows up
in a real answer, and what fixing it looks like. The heading must be the exact
category name, because the same names are used in `schemas.py` and
`eval/test_set.csv`:

- `## no_clarifying_questions`
- `## no_user_segmentation`
- `## no_prioritization`
- `## no_success_metrics`
- `## no_tradeoffs`
- `## unstructured`
- `## no_business_impact`
- `## vague_solution`

Keep each section to about 80–150 words. Short, specific sections retrieve better
than long general ones. The file starts with one example of each kind.

---

## 3. `sample_transcript.json` — the one-click demo

The app's "Try a demo transcript" button loads this file, so a visitor can see a
full feedback report without doing an interview (directives §5.4).

Write one realistic interview: the interviewer's questions and a candidate's
answers, as a list of `["assistant", "..."]` and `["user", "..."]` pairs, in
order. **Plant one or two weaknesses on purpose** (for example, an answer with no
success metric) so the demo report has something real to point out. The file
starts with a short example you can extend.

---

## Sources

List every outside source you used to write these files, and why we are allowed
to use it.

- (none yet)
