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
* Attending the Oct 23 workshop? Yes

### 1. The project, as it stands today

* **Who the user is:** An MBA student preparing for a Product Manager internship or full-time job interview for a B2B technology company.
* **The task, in one sentence:** To practice answering PM interview questions in a realistic written mock-interview setting and receive actionable feedback to improve future performance.
* **The user's input, and what comes back to the user:** The candidate types answers to four B2B PM written case questions and adaptive follow-ups. The intended output is a final structured report with strengths, weakness tags, and actionable suggestions.
* **Every source the app reads (§3.2):**
  * Lenny’s Data: https://github.com/LennysNewsletter/lennys-newsletterpodcastdata and evidence of permitted use as a free subscriber with [jgamboa@bu.edu](mailto:jgamboa@bu.edu) of Lenny’s Substack Newsletter https://prnt.sc/qf_vdsza8EKz
  * 5 job postings for current PM roles which are publicly shared in each company’s linkedin or web pages: https://drive.google.com/drive/folders/19T9uIWG9JZUat56vrQfVPImY9JGVpvjz?usp=drive_link
  * Original questions and rubrics written by our team based on linkedin experts information about interview’s structures supported by AI assistance (in process)
  * The Gemini API free tier, used only as the language model.

### 2. What changed since the proposal

* **What we changed in what we build or how we build it, and why:** We do not ask the user which type of company anymore. The current draft focuses on four fixed text-only B2B questions with adaptive follow-ups and the final report. This makes feedback quality testable within a narrow demo.
* **What the proposal feedback asked for, and what we did about it:**
  * It said to back up our sources, which we did in the sources section.
  * It also asked to specify whether job descriptions were pasted by the user or collected by us and from where, so we made sure to include this information in the sources section as well.
  * It also asked to acknowledge that if our test users are real people we need written consent on their personal data management, so we plan to make them sign a clear consent (what data is stored, why, and which third parties would have access to it) when they test our product.
  * It also asked for a real scope cut, so we decided to replace the company-type selector with a four fixed question set for B2B companies and fixed follow-ups per question.
  * It also asked to change our success metric, so we followed your suggestion and decided to set our success metric as the % of planted weaknesses the app identifies, using a set of 20 answers written by our team, each with a different planted weakness. We will also add a quick set of knowledge or satisfaction questions at the end of each session as a secondary metric, to capture something our main metric can’t: whether the app is actually useful to the user.
  * We also updated the proof of concept by adding a test set-up and the division of the plan for the presentation. 

### 3. Where the build stands

**What a user can do on the deployed app today:** We have an MVP in main and are working to make it run. The intended flow is a four-question typed interview with adaptive follow-ups and a final feedback report. A working end-to-end session on the deployed URL has not yet been confirmed.

**Capabilities from §5.1:**

| Capability | Where it fires | Status |
| --- | --- | --- |
| Structured output | Follow up and feedback steps ask the model for JSON. Our code parses it, validates fields, and drops tags that are not on the allowed list. Parse failures use a fallback question or one retry. | Working. Known gap: no fixed response schema yet, so types can slip through. |
| Retrieval | Rubric snippets are embedded. The closest three to the student's answers are added to the feedback prompt, so they change the report. | In progress. Only 7 draft snippets, and follow-up questions do not use retrieval yet. |
| Tool calling | A function the model chooses to call, such as a rubric lookup by weakness tag, whose result changes the feedback. | Not started. |

**Architecture diagram sketch:** ![Architecture Diagram](docs/architecture-diagram.jpg)

### 4. Success metric

* **The one number:** Weakness tag recall. Of the weaknesses we deliberately plant in test answers, the share that the feedback report tags correctly. It is computed by `eval/run_eval.py`, not judged by eye.
* **Where the test inputs will come from:** At least 20 realistic PM case answers, written or collected by team members and classmates who consent to this use. They include awkward ones: very short answers, off-topic answers, and confident but flawed answers. For these "awkward" ones, we may rely on AI-generated answers.
* **How expected results are recorded:** The planted weaknesses for each answer are written into `eval/test_set.csv` before any run, so correctness is never decided after seeing the output.

### 5. Proof of concept: two test inputs

**Test setup:** Both cases answer the first question in `prompts.py`: "You are the PM for a B2B SaaS tool used by finance teams to approve invoices. Customers say approvals take too long. How would you approach this?" Expected weakness tags below are written before running, not observed results. Each answer is tested in a full four question session, with the remaining answers held constant, before comparing final reports.

**Input A, ordinary candidate answer:** I would first establish where the delay occurs: incomplete invoice data, unclear ownership, or too many approval handoffs. I would segment customers by company size and approval complexity, then interview accounts payable managers and approvers while reviewing timestamps from each workflow stage. If handoffs are the main bottleneck, I would pilot automated reminders and escalation rules with mid market customers before investing in a full workflow redesign. That is lower effort than replacing the approval system and preserves current audit trails. I would compare the pilot with the current process before expanding it.

**Expected A, written before running:** The follow up should ask which specific KPI and baseline would show whether the pilot worked. The final report should flag no_success_metric (the answer promises a comparison but never defines a measurable outcome, such as median invoice approval time). It should recognize the sound diagnosis, segmentation and phased rollout, and not invent extra weaknesses.

**Returned A:** Not run yet.

**Input B, confident but flawed answer (expected to fail):** I would remove manual approvals for all invoices under $50,000 and roll the change out to every enterprise customer in the next release. Our north star target would be 90% of invoices approved within 24 hours. This is the obvious solution because humans cause the delay, so I would skip customer interviews and a pilot. If approval speed improves, I would consider the launch a success even without checking how the change affects financial controls, auditability, or fraudulent payments.

**Expected B, written before running:** The follow up should challenge the assumption that removing approvals improves the product and ask about control or fraud risk. The final report should flag no_tradeoffs_or_risks (missing controls and unintended consequences), no_clear_problem_framing (solution chosen before diagnosing the root cause) and no_user_segmentation (blanket rollout). Likely failure: the model over rewards the concrete 90% / 24 hour target and gives an overly positive assessment despite a dangerous recommendation.

**Returned B:** Not run yet.

### 6. The plan to our presentation

**Build priority:** A credible, measurable, text only B2B PM interview by the Nov 9 presentation. Feedback quality and a reliable end to end flow come before feature breadth.

**Left to build (owners match the project board):**

* **Tool calling: Max, by Oct 30.** A model invoked rubric lookup (`lookup_rubric_by_tag`) whose returned evidence changes the feedback. Ordinary Python retrieval does not count as tool calling.
* **20 row test set with expected results: Jacobo, by Oct 28.** Answers and independently labeled expected tags committed to `eval/test_set.csv` before any scoring run.
* **Request cap fix so Start over does not reset it: Caitlin, by Oct 26.** Move the quota counter outside the resettable interview state; regression test consecutive sessions.
* **Retry button for a failed report: Caitlin, by Oct 26.** Keep the transcript after a formatting failure; every retry counts against the cap.
* **Pin requirements.txt and test a cold start: Caitlin, by Oct 27.** Confirm the deployed URL loads after a clean Streamlit Cloud restart with the rubric file included.
* **Replace starter content, owner names and rubric snippets: Jimena (content), Max (integration), by Oct 29.** Final questions, prompts and rubric snippets, with provenance and permission documented; confirm retrieval grounds the final report.
* **Cost analysis from measured token counts: Max, by Nov 3.** Measured generation and embedding tokens per full mock interview, converted to cost, with free tier limits noted.
* **End to end QA and demo rehearsal: Jacobo (QA), full team (demo), by Nov 6.** Run Inputs A and B plus the full test set, check tags and failure paths, confirm one clean live session, rehearse the demo.

**Cut first if behind:** Reduce follow ups from three to one, asked only after the first question, in line with the scope cut in section 2 (fixed follow ups per question). We keep the four question text interview, the final feedback report with retrieval, the locked evaluation, the working deployment and all three required capabilities.

**Not building:** Voice, company type or role modes, user profiles, or retrieval for follow up questions.

### 7. What we need from you

We plan to measure the share of planted weaknesses the final report tags correctly. Is that an appropriate primary metric for useful PM interview feedback, and how should we account for false positive tags so the app cannot score well by flagging everything? Related: are weakness labels written by our own team an acceptable ground truth, or do we need a second labeller?
