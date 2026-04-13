import re

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from seminar_compass.web import app

client = TestClient(app)


def test_input_page_has_example_support_guidance_and_history_fields():
    response = client.get("/")

    assert response.status_code == 200
    assert "Quick start: edit this example text" in response.text
    assert "Optional support material (separate from primary outputs)" in response.text
    assert "Internal beta scope" in response.text
    assert "Supported now:" in response.text
    assert "Not supported yet:" in response.text
    assert "Optional title" in response.text
    assert "Optional one-line note" in response.text
    assert "Selected mode" in response.text
    assert "View saved history" in response.text


def test_result_page_saves_history_and_history_item_reopens():
    response = client.post(
        "/raw-text",
        data={
            "content": "Main claim. If condition applies, do action. Example details.",
            "support_materials": "Support context one.\n---\nSupport context two.",
            "title": "My seminar run",
            "note": "One-line note",
            "selected_mode": "preview",
        },
    )

    assert response.status_code == 200
    assert "Saved history metadata" in response.text
    assert "Selected mode for this run:" in response.text
    assert "preview" in response.text
    assert "Mode differences (quick view)" in response.text
    assert "When to use" in response.text
    assert "Summary output" in response.text
    assert "<strong>base</strong>" in response.text
    assert "<strong>preview</strong>" in response.text
    assert "<strong>review</strong>" in response.text
    assert "<strong>easier</strong>" in response.text

    match = re.search(r"Saved history item ID:</strong>\s*([a-f0-9-]+)", response.text)
    assert match is not None
    item_id = match.group(1)

    history_response = client.get("/history")
    assert history_response.status_code == 200
    assert "Saved history" in history_response.text
    assert "My seminar run" in history_response.text
    assert "One-line note" in history_response.text
    assert f'/history/{item_id}' in history_response.text

    reopen_response = client.get(f"/history/{item_id}")
    assert reopen_response.status_code == 200
    assert "Reconstruction Result" in reopen_response.text
    assert "My seminar run" in reopen_response.text
    assert "One-line note" in reopen_response.text


