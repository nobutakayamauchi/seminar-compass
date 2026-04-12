import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from seminar_compass.web import app


client = TestClient(app)


def test_get_root_returns_200():
    response = client.get("/")

    assert response.status_code == 200


def test_get_root_shows_mode_and_support_inputs():
    response = client.get("/")

    assert response.status_code == 200
    body = response.text.lower()
    assert "<select" in body
    assert "base" in body and "preview" in body and "review" in body and "easier" in body
    assert "support_materials" in body


def test_post_raw_text_returns_200_and_expected_sections():
    response = client.post(
        "/raw-text",
        data={
            "content": "Main claim sentence. Supporting detail. Another point.",
            "mode": "preview",
            "support_materials": "Helpful reference paragraph.",
        },
    )

    assert response.status_code == 200
    body = response.text.lower()
    assert "selected mode" in body
    assert "top 3 takeaways" in body or "main claim" in body
    assert "supplemental explanation (separate)" in body
