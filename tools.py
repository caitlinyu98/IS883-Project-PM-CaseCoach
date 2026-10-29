# --- tools the interviewer model can choose to call ---
# AI-assisted starter code (Claude, Anthropic). Review and edit before committing.
#
# The model reads each function's docstring and decides on its own when to call it.
# That decision is what makes this real tool calling (directives §5.1, item 2).
# Every call is written to st.session_state.tool_log so you can show where it fired.

import json
import random
import streamlit as st
from retrieval import search

with open("data/questions.json") as f:
    QUESTIONS = json.load(f)


def get_question(question_type: str) -> dict:
    """Get the next interview question. question_type must be one of:
    product_design, metrics, prioritization, strategy, behavioral."""
    asked = st.session_state.setdefault("asked_ids", [])
    pool = [q for q in QUESTIONS if q["type"] == question_type and q["id"] not in asked]
    if not pool:
        return {"error": "No unused questions of that type. Pick another type."}
    q = random.choice(pool)
    asked.append(q["id"])
    st.session_state.tool_log.append(f"get_question({question_type}) -> {q['id']}")
    return {"id": q["id"], "question": q["question"]}


def get_rubric(topic: str) -> dict:
    """Look up what a strong PM interview answer includes for a topic or question.
    Call this before writing a follow-up question, to target what the answer missed."""
    hits = search(st.session_state.client, topic, k=3)
    st.session_state.tool_log.append(f"get_rubric({topic}) -> {[h['id'] for h in hits]}")
    return {"rubric_excerpts": [h["text"] for h in hits]}
