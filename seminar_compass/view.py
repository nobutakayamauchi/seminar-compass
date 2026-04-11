from __future__ import annotations

from seminar_compass.models import ReconstructionOutput


def render_result_view(output: ReconstructionOutput) -> str:
    """Render a minimal user-facing result view for one reconstruction output."""
    lines = [
        f"Output type: {output.output_type.value}",
        "",
        "Top 3 takeaways:",
        *[f"- {item}" for item in output.top_takeaways],
        "",
        "Main claim:",
        output.main_claim,
        "",
        "Conditions / assumptions:",
        *[f"- {item}" for item in output.conditions_assumptions],
        "",
        "Practical takeaway:",
        output.practical_takeaway,
        "",
        "Prerequisite knowledge:",
        *[f"- {item}" for item in output.prerequisite_knowledge],
        "",
        "What to consume first:",
        *[f"- {item}" for item in output.what_to_watch_read_first],
        "",
        "Safely skippable parts:",
        *[f"- {item}" for item in output.safely_skippable_parts],
        "",
        "Original-order summary:",
        output.original_order_summary,
        "",
        "Reconstructed summary:",
        output.reconstructed_summary,
        "",
        "3-line reactivation summary:",
        *[f"- {item}" for item in output.reactivation_3line],
        "",
        "Retrieval questions:",
        *[f"- {item}" for item in output.retrieval_questions],
        "",
        "Confidence note:",
        output.confidence_note,
        "",
        "Supplemental explanation (separate):",
        output.supplemental_explanation or "None",
    ]
    return "\n".join(lines)
