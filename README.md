## Workshop checkpoint

Team name: Team 7, PM CaseCoach

Members:

* Jimena Gamboa, [jgamboa@bu.edu](mailto:jgamboa@bu.edu)
* Max Lattermann, [mlatterm@bu.edu](mailto:mlatterm@bu.edu)
* Jacobo Naranjo Guerrero, [jacobon@bu.edu](mailto:jacobon@bu.edu)
* Caitlin Yu, [caitliny@bu.edu](mailto:caitliny@bu.edu)

### 0. Team infrastructure

* GitHub repository: https://github.com/caitlinyu98/IS883-Project-PM-CaseCoach
* Project board (GitHub Projects, §5.7): https://github.com/users/caitlinyu98/projects/1
* Streamlit app URL: https://is883-project-pm-casecoach.streamlit.app/
* Attending the Oct 23 workshop? [yes / no]

### 1. The project, as it stands today

* **Who the user is:** An MBA student preparing for Product Manager interviews who wants realistic case practice and has no interviewer available on demand.
* **Today they practise by** doing mock interviews with classmates, reading case frameworks, or rehearsing alone. Partners are hard to schedule and their feedback is inconsistent.
* **The task, in one sentence:** The student answers a PM case question in writing, the app plays the interviewer with adaptive follow up questions, and then returns a structured feedback report that tags the weaknesses in the answers and points to the matching rubric guidance.
* **The user's input, and what comes back:** Input is the student's typed answers to a case question and its follow ups. Back come follow up questions during the interview, then a feedback report with weakness tags, a short explanation for each, and rubric guidance retrieved for those weaknesses.
* **Every source the app reads (§3.2):**
  * `sources/rubrics.json`: PM case interview rubric snippets written by our team. We own this content, so no licensing issue. It is currently draft starter content that we will rewrite.
  * Case prompts and test answers: written by our team, or contributed by classmates who agreed in writing to this specific use. No personal data is scraped and no website is read.
  * The Gemini API free tier, used only as the language model.

### 2. What changed since the proposal

* **What we changed:** [JIMENA: state what changed in what we build or how, and why. Write "none" if nothing.]
  * Current state worth recording: a working scaffold exists on the `starter-scaffold` branch (PR #1) and is not yet merged into `main`. It has the interview loop, JSON structured output with validation, a first version of retrieval over the rubric snippets, a prompt version variable, and a basic request cap.
* **What the proposal feedback asked for, and what we did:** [JIMENA: paste the feedback points and our response to each.]

### 3. Where the build stands

**What a user can do on the deployed app today:** [CONFIRM against the live URL. If the live app is still the placeholder, write that plainly and say the working version is on the `starter-scaffold` branch.]

**Capabilities from §5.1:**

| Capability | Where it fires | Status |
| --- | --- | --- |
| Structured output | Follow up and feedback steps ask the model for JSON. Our code parses it, validates fields, and drops tags that are not on the allowed list. Parse failures use a fallback question or one retry. | Working. Known gap: no fixed response schema yet, so types can slip through. |
| Retrieval | Rubric snippets are embedded. The closest three to the student's answers are added to the feedback prompt, so they change the report. | In progress. Only 7 draft snippets, and follow up questions do not use retrieval yet. |
| Tool calling | A function the model chooses to call, such as a rubric lookup by weakness tag, whose result changes the feedback. | Not started. |

**Architecture diagram sketch:** [COMMIT AN IMAGE, for example `docs/architecture_v0.png`, AND LINK IT HERE. It should show input, each stage, where the model is called, where each capability fires, and the failure path.]

### 4. Success metric

* **The one number:** Weakness tag recall. Of the weaknesses we deliberately plant in test answers, the share that the feedback report tags correctly. It is computed by `eval/run_eval.py`, not judged by eye.
* **Where the test inputs will come from:** At least 20 realistic PM case answers, written or collected by team members and classmates who consent to this use. They include awkward ones: very short answers, off topic answers, and confident but flawed answers.
* **How expected results are recorded:** The planted weaknesses for each answer are written into `eval/test_set.csv` before any run, so correctness is never decided after seeing the output.

### 5. Proof of concept: two test inputs

**Input A, an ordinary input.**
* Input: A full paragraph answer to a standard product case, for example "How would you improve a food delivery app's order tracking?", that gives a goal and users but offers no success metrics and no prioritisation.
* Expected result, written before running: The report should tag the missing success metrics and missing prioritisation, should not invent other weaknesses, and should show rubric guidance for those two tags. [MATCH TAG NAMES TO `sources/rubrics.json`.]
* What the app returned: [not run yet. Fill after running.]

**Input B, an input we expect it to get wrong.**
* Input: A confident answer with plausible sounding structure whose logic is flawed, for example a recommendation based on a number the candidate never justifies.
* Expected result, written before running: Our rubric tags are broad, so we expect the app to miss the flawed reasoning and return a generic pass or an irrelevant tag. This is the kind of failure our metric may not catch. [REFINE OR REPLACE WITH A REAL ANSWER.]
* What the app returned: [not run yet. Fill after running.]

### 6. The plan to our presentation

| Task | Owner | End date |
| --- | --- | --- |
| Build tool calling, such as a rubric lookup by tag, and wire it into feedback | [OWNER] | [DATE] |
| Write the 20 row test set with planted weaknesses recorded in advance | [OWNER] | [DATE] |
| Fix the request cap so Start over does not reset it, and count embedding and retry calls | [OWNER] | [DATE] |
| Add a retry button for a failed report, and a clear missing key message | [OWNER] | [DATE] |
| Pin `requirements.txt` and test a cold start | [OWNER] | [DATE] |
| Replace starter content, rewrite rubric snippets, put real owner names in file headers | [OWNER] | [DATE] |
| Measure token cost per interaction for the cost analysis | [OWNER] | [DATE] |
| Architecture diagram, kept in step with the code | [OWNER] | [DATE] |

These rows must match the cards on the project board.

**What we cut first if behind:** Retrieval for follow up questions. We keep retrieval in the feedback step only.

### 7. What we need from you

How should we score an open ended case answer with a number a program can compute? We plan to use tag recall against weaknesses we label ourselves, and we want to know whether labels written by our team are an acceptable ground truth, or whether we need a second labeller.
