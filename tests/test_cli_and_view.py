import subprocess
import sys

from seminar_compass import InputType, ReconstructionRequest, SeminarCompassPipeline
from seminar_compass.view import render_result_view


def test_result_view_contains_required_sections():
    pipeline = SeminarCompassPipeline()
    response = pipeline.reconstruct(
        ReconstructionRequest(
            input_type=InputType.RAW_TEXT,
            content="Main claim. If this holds, do X. Example detail.",
            support_materials=["Reference support detail."],
        )
    )
    rendered = render_result_view(response.primary_outputs[0])

    expected_sections = [
        "Top 3 takeaways:",
        "Main claim:",
        "Conditions / assumptions:",
        "Practical takeaway:",
        "Prerequisite knowledge:",
        "What to consume first:",
        "Safely skippable parts:",
        "Original-order summary:",
        "Reconstructed summary:",
        "3-line reactivation summary:",
        "Retrieval questions:",
        "Confidence note:",
        "Supplemental explanation (separate):",
    ]
    for section in expected_sections:
        assert section in rendered


def test_cli_raw_text_entrypoint_works():
    cmd = [
        sys.executable,
        "-m",
        "seminar_compass.cli",
        "--text",
        "Main claim. If condition applies, do action. Example details.",
        "--mode",
        "base",
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)

    assert result.returncode == 0
    assert "Main claim:" in result.stdout
    assert "Top 3 takeaways:" in result.stdout
