# --- structured output: the shape of the feedback report ---
# AI-assisted starter code (Claude, Anthropic). Review and edit before committing.
#
# The model must return JSON in exactly this shape. The `category` values must
# match the weakness categories in data/rubrics.md and eval/test_set.csv,
# because that is how the evaluation scores the metric automatically.

from typing import Literal
from pydantic import BaseModel

Category = Literal[
    "no_clarifying_questions",  # jumped into a solution without scoping the problem
    "no_user_segmentation",     # did not identify the users or buyers
    "no_prioritization",        # listed ideas without choosing or ranking them
    "no_success_metrics",       # no way to measure whether it worked
    "no_tradeoffs",             # did not weigh risks, costs or alternatives
    "unstructured",             # no clear framework or order
    "no_business_impact",       # ignored revenue, retention or the B2B buyer
    "vague_solution",           # too generic to act on
]


class Weakness(BaseModel):
    category: Category
    evidence: str      # what in the answer shows this weakness
    how_to_fix: str


class FeedbackReport(BaseModel):
    overall_score: int          # 1 to 5, clamped in app.py
    strengths: list[str]
    weaknesses: list[Weakness]
    recommendations: list[str]
