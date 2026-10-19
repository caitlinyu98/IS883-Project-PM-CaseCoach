# Written with Claude (Anthropic) as coding assistant. Log the exchange in the GenAI appendix.
# --- Caitlin: rubric retrieval by embedding similarity (change name to the real owner) ---
import json
import os
import numpy as np
from llm import embed

RUBRIC_PATH = os.path.join(os.path.dirname(__file__), "sources", "rubrics.json")
_index = None


def _build_index():
    global _index
    if _index is None:
        with open(RUBRIC_PATH, encoding="utf-8") as f:
            items = json.load(f)
        vecs = np.array(embed([i["title"] + ". " + i["text"] for i in items]), dtype=float)
        vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
        _index = (items, vecs)
    return _index


def retrieve(query, k=3):
    """Return the k rubric snippets closest to the query. Raises LLMError if embeddings fail."""
    items, vecs = _build_index()
    q = np.array(embed([query])[0], dtype=float)
    q = q / np.linalg.norm(q)
    scores = vecs @ q
    top = np.argsort(-scores)[:k]
    return [dict(items[i], score=float(scores[i])) for i in top]
