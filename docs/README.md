# docs/ — the architecture diagram

Save the diagram here as `architecture.png` (directives §5.2). It goes in the
report and on a slide, and it is compared against the code in Q&A, so it must
match what the code actually does.

Draw it however you like (draw.io, Figma, a whiteboard photo). It must show:

1. **What goes in and what comes out:** the candidate's typed answers in, the
   feedback report out.
2. **Every stage in between,** in order:
   - `app.py` receives the answer
   - Interviewer model call, labeled **`INTERVIEWER_V2`** (the prompt name)
   - Tool calls the model chooses: **`get_question`** (reads `data/questions.json`)
     and **`get_rubric`** (calls `retrieval.py`, which searches the embeddings)
   - Feedback model call, labeled **`FEEDBACK_V2`**, with the retrieved rubric
   - JSON parsed into **`FeedbackReport`** (`schemas.py`)
   - Report shown to the candidate
3. **Where each capability fires:** tool calling, retrieval, structured output
   (and structured prompting if you claim it).
4. **The failure path:** API error → retry once → error message; JSON that does
   not parse → retry once → error message; request cap reached → warning.

Update the diagram whenever the code changes. A diagram that does not match the
code costs more than no diagram.
