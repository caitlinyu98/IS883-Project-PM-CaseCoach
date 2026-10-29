# --- retrieval over our question bank and rubrics ---
# AI-assisted starter code (Claude, Anthropic). Review and edit before committing.
#
# How it works:
# 1. Every question and every "## " section of data/rubrics.md becomes a chunk.
# 2. Each chunk is turned into an embedding (a list of numbers) once per app start.
# 3. search() embeds the query and returns the k chunks whose numbers are closest.

import json
import numpy as np
import streamlit as st
from config import EMBED_MODEL


def load_chunks():
    chunks = []
    with open("data/questions.json") as f:
        for q in json.load(f):
            chunks.append({
                "id": q["id"],
                "text": f"{q['question']}\nStrong answer includes: {q['strong_answer_includes']}",
            })
    with open("data/rubrics.md") as f:
        sections = f.read().split("\n## ")
    for i, section in enumerate(sections):
        section = section.strip().lstrip("# ").strip()
        if len(section) > 30:  # skip the file title and empty sections
            chunks.append({"id": f"rubric_{i}", "text": section})
    return chunks


@st.cache_resource  # embed once per app start, not on every click
def build_index(_client):
    chunks = load_chunks()
    result = _client.models.embed_content(model=EMBED_MODEL, contents=[c["text"] for c in chunks])
    vecs = np.array([e.values for e in result.embeddings])
    vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    return chunks, vecs


def search(client, query, k=3):
    chunks, vecs = build_index(client)
    q = np.array(client.models.embed_content(model=EMBED_MODEL, contents=query).embeddings[0].values)
    scores = vecs @ (q / np.linalg.norm(q))
    top = scores.argsort()[::-1][:k]
    return [{**chunks[i], "score": float(scores[i])} for i in top]
