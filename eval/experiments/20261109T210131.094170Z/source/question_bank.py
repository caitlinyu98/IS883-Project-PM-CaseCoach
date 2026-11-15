# Written with Claude (Anthropic) as coding assistant. Log the exchange in the GenAI appendix.
# --- Caitlin: question bank loader and interview picker (bank format from starter-scaffold) ---
#
# Questions live in data/questions.json, each with an id, a type, the question text, and what a
# strong answer includes. Code (not the model) picks the questions for an interview, so every
# session is short, predictable, and cheap in API calls.
import json
import os
import random

BANK_PATH = os.path.join(os.path.dirname(__file__), "data", "questions.json")

with open(BANK_PATH, encoding="utf-8") as f:
    QUESTIONS = json.load(f)

BY_ID = {q["id"]: q for q in QUESTIONS}  # used by eval/run_eval.py to look up a question by id


def pick_interview(n, rng=random):
    """Pick n questions: a different type for each while types last, in random order."""
    types = sorted({q["type"] for q in QUESTIONS})
    rng.shuffle(types)
    picked = [rng.choice([q for q in QUESTIONS if q["type"] == t]) for t in types[:n]]
    rest = [q for q in QUESTIONS if q not in picked]
    rng.shuffle(rest)
    return picked + rest[: n - len(picked)]
