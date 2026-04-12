import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from seminar_compass.web import app

client = TestClient(app)


def test_input_page_has_example_and_support_guidance():
    response = client.get("/")

    assert response.status_code == 200
    assert "Quick start: edit this example text" in response.text
    assert "Optional support material (separate from primary outputs)" in response.text


def test_result_page_shows_mode_differences_and_preserves_sections():
    response = client.post(
        "/raw-text",
        data={
            "content": "Main claim. If condition applies, do action. Example details.",
            "support_materials": "Support context one.\n---\nSupport context two.",
        },
    )

    assert response.status_code == 200
    assert "Mode differences (quick view)" in response.text
    assert "When to use" in response.text
    assert "Summary output" in response.text
    assert "<strong>base</strong>" in response.text
    assert "<strong>preview</strong>" in response.text
    assert "<strong>review</strong>" in response.text
    assert "<strong>easier</strong>" in response.text
    assert "Use before committing time to the full source." in response.text

    # Existing base output sections remain present.
    assert "Top 3 takeaways" in response.text
    assert "Main claim" in response.text
    assert "Conditions / assumptions" in response.text
    assert "Supplemental explanation (separate)" in response.text
    assert "Supplemental explanation (separate from primary summary)" in response.text
