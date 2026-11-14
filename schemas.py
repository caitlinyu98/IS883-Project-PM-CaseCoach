# Written with Claude (Anthropic) as coding assistant. Log the exchange in the GenAI appendix.
# --- Caitlin: structured output schema for the feedback report (ported from starter-scaffold) ---
#
# Gemini is given this schema (response_schema) so it must answer in exactly this shape.
# Our code then validates the answer against the same schema: if it does not fit,
# feedback.py retries once and then shows the "could not format" message.
# Expanded from seven to ten weaknesses on November 14, 2026, before corrected evaluation.
# Recall remains the primary workshop metric; historical seven-tag results are not directly comparable.

from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

Tag = Literal[
    "no_success_metric",
    "no_user_segmentation",
    "no_clear_problem_framing",
    "no_prioritization_rationale",
    "no_tradeoffs_or_risks",
    "off_topic",
    "empty_or_too_short",
    "no_business_impact",
    "vague_solution",
    "unstructured",
]


class Weakness(BaseModel):
    tag: Tag
    evidence: str  # what the candidate said, or failed to say, that shows the weakness
    fix: str       # one concrete action the candidate can take


class FeedbackReport(BaseModel):
    model_config = ConfigDict(strict=True)
    overall_score: int = Field(ge=1, le=10, description="Overall interview score 1 to 10, including off-topic and insufficient answers")
    overall_summary: str
    strengths: list[str]
    weaknesses: list[Weakness]
    next_steps: list[str]


class RelevanceItem(BaseModel):
    index: int
    status: Literal["relevant", "partial", "off_topic"]
    reason: str

class RelevanceResult(BaseModel):
    items: list[RelevanceItem]

class FollowupResult(BaseModel):
    model_config = ConfigDict(strict=True)
    in_scope: bool
    follow_up: str
