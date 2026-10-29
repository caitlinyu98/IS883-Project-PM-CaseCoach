# PM Case Coach

**IS883 Fall 2026 · Team 7** · Jimena Gamboa, Max Lattermann, Jacobo Naranjo Guerrero, Caitlin Yu

A Streamlit app where an MBA student practices a B2B SaaS product manager
interview. A Gemini model plays the interviewer: it picks questions from our
question bank, asks follow-ups that target what each answer missed, and ends with
a structured feedback report of strengths, weaknesses and next steps.

- **Live app:** _(paste the Streamlit URL here)_
- **Project board:** _(paste the GitHub Projects link here)_
- **API key:** stored only in Streamlit Cloud → app Settings → Secrets. Never in this repo.

---

## What is in this repo

| File or folder | What it is | Owner |
| --- | --- | --- |
| `app.py` | The Streamlit app the user sees: chat, buttons, feedback report, request cap 
| `config.py` | Model names, limits and settings in one place 
| `prompts.py` | Every prompt sent to the model, versioned (V1, V2) 
| `schemas.py` | The shape the feedback report must come back in (structured output) 
| `tools.py` | Functions the interviewer model chooses to call (tool calling) 
| `retrieval.py` | Embeddings + similarity search over our own content (retrieval) 
| `data/` | Question bank, rubrics and demo transcript, written by us. See `data/README.md` 
| `eval/` | Test set and scoring notebook. See `eval/README.md` 
| `docs/` | Architecture diagram. See `docs/README.md` 

## How to run it on your laptop

1. `pip install -r requirements.txt`
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and paste your key.
3. `streamlit run app.py`

