# Written with Claude (Anthropic) as coding assistant. Log the exchange in the GenAI appendix.
# --- Caitlin: adaptive follow up question and scope check (change name to the real owner) ---
from llm import generate_json, ParseError
from prompts import FOLLOWUP_PROMPTS, ACTIVE_VERSION, FALLBACK_FOLLOWUP


def generate_followup(question, answer, version=ACTIVE_VERSION):
    """Returns {"in_scope": bool, "follow_up": str, "fallback_used": bool}.
    Raises LLMError on API failure (caller shows a message). Unparseable output uses a fixed fallback."""
    user = f"Interview question:\n{question}\n\nCandidate answer:\n{answer}"
    try:
        data = generate_json(FOLLOWUP_PROMPTS[version], user)
        in_scope = bool(data["in_scope"])
        follow_up = str(data.get("follow_up", "")).strip()
        if in_scope and not follow_up:
            raise KeyError("missing follow_up")
    except (ParseError, KeyError, TypeError, AttributeError):
        return {"in_scope": True, "follow_up": FALLBACK_FOLLOWUP, "fallback_used": True}
    return {"in_scope": in_scope, "follow_up": follow_up, "fallback_used": False}
