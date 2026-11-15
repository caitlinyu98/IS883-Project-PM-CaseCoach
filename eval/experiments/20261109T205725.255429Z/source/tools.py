import json
import os
from collections.abc import Callable

RUBRIC_PATH = os.path.join(os.path.dirname(__file__), "sources", "rubrics.json")


def lookup_rubric_by_tag(tag: str) -> dict[str, str]:
    """Look up one feedback rubric by its weakness tag."""
    with open(RUBRIC_PATH, encoding="utf-8") as rubric_file:
        rubrics = json.load(rubric_file)

    for rubric in rubrics:
        if rubric["tag"] == tag:
            return rubric
    raise ValueError(f"No rubric found for tag: {tag}")


def create_lookup_rubric_tool(
    call_log: list[dict[str, object]],
    tool_results: list[dict[str, str]],
) -> Callable[[str], dict[str, str]]:
    """Create the model-callable lookup function and record its result."""
    def tracked_lookup_rubric_by_tag(tag: str) -> dict[str, str]:
        rubric = lookup_rubric_by_tag(tag)
        call_log.append({
            "name": "lookup_rubric_by_tag",
            "argument": {"tag": tag},
            "result_id": rubric["tag"],
        })
        tool_results.append(rubric)
        return rubric

    tracked_lookup_rubric_by_tag.__name__ = "lookup_rubric_by_tag"
    tracked_lookup_rubric_by_tag.__doc__ = (
        "Look up a rubric by weakness tag. Valid tags: no_success_metric, "
        "no_user_segmentation, no_clear_problem_framing, "
        "no_prioritization_rationale, no_tradeoffs_or_risks, off_topic, "
        "empty_or_too_short."
    )
    return tracked_lookup_rubric_by_tag
