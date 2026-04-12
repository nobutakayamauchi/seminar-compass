from io import BytesIO

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

import seminar_compass.web as web


client = TestClient(web.app)


class _FakeResponse:
    def __init__(self, body: str, content_type: str = "text/html") -> None:
        self._io = BytesIO(body.encode("utf-8"))
        self.headers = {"Content-Type": content_type}

    def read(self, n: int = -1) -> bytes:
        return self._io.read(n)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_get_root_returns_200():
    response = client.get("/")

    assert response.status_code == 200


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


def test_post_raw_text_empty_returns_clear_error():
    response = client.post(
        "/raw-text",
        data={"content": "   ", "mode": "base", "support_materials": ""},
    )

    assert response.status_code == 400
    assert "please paste raw text before submitting." in response.text.lower()


def test_url_form_path_exists():
    response = client.get("/")

    assert response.status_code == 200
    assert 'action="/url"' in response.text.lower()


def test_simple_extractable_url_flows_into_reconstruction(monkeypatch):
    html = "<html><body><p>Main claim sentence.</p><p>Supporting detail.</p><p>Third point here.</p></body></html>"

    def fake_urlopen(url, timeout=8):  # noqa: ARG001
        return _FakeResponse(html)

    monkeypatch.setattr(web, "urlopen", fake_urlopen)

    response = client.post(
        "/url",
        data={"url": "https://example.com/page", "mode": "base", "support_materials": ""},
    )

    assert response.status_code == 200
    assert "main claim" in response.text.lower()


def test_url_extraction_failure_returns_clear_error(monkeypatch):
    def fake_urlopen(url, timeout=8):  # noqa: ARG001
        raise web.URLError("failure")

    monkeypatch.setattr(web, "urlopen", fake_urlopen)

    response = client.post("/url", data={"url": "https://example.com/fail", "mode": "base"})

    assert response.status_code == 400
    assert "could not extract readable text from the provided url." in response.text.lower()


def test_url_invalid_input_returns_clear_error():
    response = client.post("/url", data={"url": "not-a-url", "mode": "base"})

    assert response.status_code == 400
    assert "please enter a valid http(s) url." in response.text.lower()
