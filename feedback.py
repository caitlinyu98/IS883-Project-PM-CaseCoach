# Written with Claude (Anthropic) as coding assistant. Log the exchange in the GenAI appendix.
# --- Caitlin: weakness taxonomy, structured report, validation, parse fallback (change name to the real owner) ---
from llm import generate_json, ParseError, LLMError
from prompts import FEEDBACK_PROMPTS, ACTIVE_VERSION
from retrieval import retrieve

MIN_WORDS = 5  # fewer total words than this is handled by a rule, not the model

TAXONOMY = {
    "no_success_metric": "No concrete success metric or way to measure it",
    "no_user_segmentation": "Does not identify or prioritize user segments",
    "no_clear_problem_framing": "Jumps to solutions without framing the problem",
    "no_prioritization_rationale": "No explicit logic for choosing between options",
    "no_tradeoffs_or_risks": "Ignores tradeoffs, risks, or how to detect being wrong",
    "off_topic": "Answer does not address the question asked",
    "empty_or_too_short": "Empty or too short to assess",
}


def transcript_to_text(transcript):
    parts = []
    for t in transcript:
        parts.append(f"Question: {t['question']}\nAnswer: {t.get('answer', '')}")
        if t.get("follow_up"):
            parts.append(f"Follow up: {t['follow_up']}\nFollow up answer: {t.get('follow_up_answer', '')}")
    return "\n\n".join(parts)


def _answers_only(transcript):
    out = []
    for t in transcript:
        out.append(t.get("answer", ""))
        out.append(t.get("follow_up_answer", ""))
    return " ".join(x for x in out if x)


def validate_report(r):
    """Deterministic check. Returns (ok, cleaned_report). Unknown tags are dropped."""
    if not isinstance(r, dict):
        return False, None
    if not isinstance(r.get("overall_summary"), str):
        return False, None
    if not isinstance(r.get("strengths"), list) or not isinstance(r.get("next_steps"), list):
        return False, None
    if not isinstance(r.get("weaknesses"), list):
        return False, None
    clean = []
    for w in r["weaknesses"]:
        if isinstance(w, dict) and w.get("tag") in TAXONOMY:
            clean.append({"tag": w["tag"], "evidence": str(w.get("evidence", "")), "fix": str(w.get("fix", ""))})
    return True, {
        "overall_summary": r["overall_summary"],
        "strengths": [str(s) for s in r["strengths"]],
        "weaknesses": clean,
        "next_steps": [str(s) for s in r["next_steps"]],
    }


def generate_report(transcript, version=ACTIVE_VERSION, use_retrieval=True):
    """Returns {"report": dict or None, "meta": {...}}. Raises LLMError on API failure."""
    meta = {"parse_ok": True, "retrieval_used": False, "retrieved_tags": [], "rule_based": False}

    # Rule, not model: an empty or tiny answer needs no language model.
    if len(_answers_only(transcript).split()) < MIN_WORDS:
        meta["rule_based"] = True
        report = {
            "overall_summary": "There was not enough of an answer to assess.",
            "strengths": [],
            "weaknesses": [{"tag": "empty_or_too_short", "evidence": "The answer was empty or only a few words.",
                            "fix": "Write a structured answer: frame the problem, name users, a metric, and tradeoffs."}],
            "next_steps": ["Try again with a full answer."],
        }
        return {"report": report, "meta": meta}

    text = transcript_to_text(transcript)

    # CAPABILITY: retrieval. Rubric snippets closest to the answers are injected into the prompt.
    rubric_block = ""
    if use_retrieval:
        try:
            hits = retrieve(_answers_only(transcript), k=3)
            rubric_block = "\n".join(f"- [{h['tag']}] {h['title']}: {h['text']}" for h in hits)
            meta["retrieval_used"] = True
            meta["retrieved_tags"] = [h["tag"] for h in hits]
        except LLMError:
            meta["retrieval_failed"] = True  # continue without retrieval, but record it

    allowed = "\n".join(f"- {k}: {v}" for k, v in TAXONOMY.items())
    user = (f"ALLOWED WEAKNESS TAGS:\n{allowed}\n\n"
            f"RUBRIC EXCERPTS:\n{rubric_block or '(none)'}\n\n"
            f"TRANSCRIPT:\n{text}")

    # CAPABILITY: structured prompting (versioned system prompt) + structured output (JSON, validated).
    for _ in range(2):  # one retry if the output does not parse or validate
        try:
            data = generate_json(FEEDBACK_PROMPTS[version], user)
        except ParseError:
            continue
        ok, clean = validate_report(data)
        if ok:
            return {"report": clean, "meta": meta}
    meta["parse_ok"] = False
    return {"report": None, "meta": meta}
