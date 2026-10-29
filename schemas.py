# Written with Claude (Anthropic) as coding assistant. Log the exchange in the GenAI appendix.
# --- Caitlin: structured output schema for the feedback report (ported from starter-scaffold) ---
#
# Gemini is given this schema (response_schema) so it must answer in exactly this shape.
# Our code then validates the answer against the same schema: if it does not fit,
# feedback.py retries once and then shows the "could not format" message.
# The tag names are the 7 tags fixed in our workshop checkpoint; eval/run_eval.py scores against them.

from typing import Literal
from pydantic import BaseModel

Tag = Literal[
    "no_success_metric",
    "no_user_segmentation",
    "no_clear_problem_framing",
    "no_prioritization_rationale",
    "no_tradeoffs_or_risks",
    "off_topic",
    "empty_or_too_short",
]


class Weakness(BaseModel):
    tag: Tag
    evidence: str  # what the candidate said, or failed to say, that shows the weakness
    fix: str       # one concrete action the candidate can take


class FeedbackReport(BaseModel):
    overall_summary: str
    strengths: list[str]
    weaknesses: list[Weakness]
    next_steps: list[str]
