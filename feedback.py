# Written with Claude (Anthropic) as coding assistant. Log the exchange in the GenAI appendix.
# --- Caitlin: weakness taxonomy, structured report, validation, parse fallback (change name to the real owner) ---
from pydantic import ValidationError
from llm import generate_json, generate_with_tools, ParseError, LLMError
from prompts import FEEDBACK_PROMPTS, ACTIVE_VERSION
from schemas import FeedbackReport
from tools import create_lookup_rubric_tool

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

SCORE_RUBRIC = (
    "OVERALL SCORE: set overall_score to an integer from 1 to 10.\n"
    "1-2 = vague, no structure, no metric, no users named\n"
    "3-4 = some structure but misses most of: problem framing, users, metric, tradeoffs\n"
    "5-6 = covers about half of: problem framing, users, metric, tradeoffs\n"
    "7-8 = covers all four with minor gaps\n"
    "9-10 = covers all four with specific, quantified, well prioritized reasoning"
)


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
    """Deterministic check: does the model's JSON fit FeedbackReport (schemas.py)?
    Returns (ok, cleaned_report). A tag outside the 7 allowed tags fails validation."""
    try:
        report = FeedbackReport.model_validate(r)
    except ValidationError as e:
        print(f"[feedback] report failed validation: {e!r}", flush=True)
        return False, None
    clean = report.model_dump()
    clean["overall_score"] = min(max(int(clean.get("overall_score", 1)), 1), 10)  # keep it in 1 to 10
    return True, clean


def generate_report(transcript, version=ACTIVE_VERSION, use_retrieval=True):
    """Returns {"report": dict or None, "meta": {...}}. Raises LLMError on API failure."""
    meta = {
        "parse_ok": True,
        "retrieval_used": False,
        "retrieved_tags": [],
        "tool_calls": [],
        "rule_based": False,
    }

    # Rule, not model: an empty or tiny answer needs no language model.
    if len(_answers_only(transcript).split()) < MIN_WORDS:
        meta["rule_based"] = True
        report = {
            "overall_score": 1,
            "overall_summary": "There was not enough of an answer to assess.",
            "strengths": [],
            "weaknesses": [{"tag": "empty_or_too_short", "evidence": "The answer was empty or only a few words.",
                            "fix": "Write a structured answer: frame the problem, name users, a metric, and tradeoffs."}],
            "next_steps": ["Try again with a full answer."],
        }
        return {"report": report, "meta": meta}

    text = transcript_to_text(transcript)

    # The model selects a rubric tag and invokes the lookup before feedback is generated.
    rubric_block = ""
    if use_retrieval:
        tool_calls = meta["tool_calls"]
        tool_results = []
        lookup_tool = create_lookup_rubric_tool(tool_calls, tool_results)
        tool_system = (
            "You are evaluating a product manager interview answer. Choose the single "
            "most relevant weakness tag based on the transcript, then call "
            "lookup_rubric_by_tag exactly once. Do not assess the answer or provide "
            "feedback; the rubric will be used in a separate feedback step."
        )
        allowed = "\n".join(f"- {tag}: {description}" for tag, description in TAXONOMY.items())
        tool_user = f"ALLOWED WEAKNESS TAGS:\n{allowed}\n\nTRANSCRIPT:\n{text}"
        function_calls = generate_with_tools(tool_system, tool_user, [lookup_tool])
        if len(function_calls) != 1:
            raise LLMError("The model must invoke lookup_rubric_by_tag exactly once.")
        function_call = function_calls[0]
        if function_call.name != "lookup_rubric_by_tag":
            raise LLMError(f"The model requested an unexpected tool: {function_call.name}.")
        arguments = function_call.args or {}
        tag = arguments.get("tag")
        if not isinstance(tag, str):
            raise LLMError("The rubric lookup tool call did not include a string tag.")
        try:
            lookup_tool(tag)
        except (OSError, ValueError, KeyError) as e:
            raise LLMError(f"Rubric lookup failed: {e}") from e
        rubric = tool_results[0]
        rubric_block = f"- [{rubric['tag']}] {rubric['title']}: {rubric['text']}"
        meta["retrieval_used"] = True
        meta["retrieved_tags"] = [rubric["tag"]]

    allowed = "\n".join(f"- {k}: {v}" for k, v in TAXONOMY.items())
    user = (f"ALLOWED WEAKNESS TAGS:\n{allowed}\n\n"
            f"{SCORE_RUBRIC}\n\n"
            f"RUBRIC TOOL EVIDENCE:\n{rubric_block or '(not requested)'}\n\n"
            f"Use the returned rubric evidence as the evaluation standard for its tag. "
            f"Only report the weakness if the transcript supports it; make the feedback "
            f"and fix specific to the rubric criterion.\n\n"
            f"TRANSCRIPT:\n{text}")

    # CAPABILITY: structured prompting (versioned system prompt) + structured output (JSON, validated).
    for _ in range(2):  # one retry if the output does not parse or validate
        try:
            data = generate_json(FEEDBACK_PROMPTS[version], user, schema=FeedbackReport)
        except ParseError as e:
            print(f"[feedback] JSON parse failed: {e!r}", flush=True)
            continue
        ok, clean = validate_report(data)
        if ok:
            return {"report": clean, "meta": meta}
    meta["parse_ok"] = False
    return {"report": None, "meta": meta}
