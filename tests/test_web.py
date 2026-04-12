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


def test_get_root_shows_url_form_path():
    response = client.get("/")

    assert response.status_code == 200
    body = response.text.lower()
    assert 'action="/url"' in body


def test_post_url_flows_into_reconstruction(monkeypatch):
    html = """
    <html><body><h1>Main claim sentence.</h1><p>Supporting detail for learning.</p><p>Third sentence here.</p></body></html>
    """

    def fake_urlopen(request, timeout=8):  # noqa: ARG001
        return _FakeResponse(html)

    monkeypatch.setattr(web, "urlopen", fake_urlopen)

    response = client.post(
        "/url",
        data={"url": "https://example.com/post", "mode": "base", "support_materials": ""},
    )

    assert response.status_code == 200
    body = response.text.lower()
    assert "main claim" in body


def test_post_url_extraction_failure_shows_clear_message(monkeypatch):
    def fake_urlopen_raise(request, timeout=8):  # noqa: ARG001
        raise web.URLError("network down")

    monkeypatch.setattr(web, "urlopen", fake_urlopen_raise)

    response = client.post("/url", data={"url": "https://example.com/bad", "mode": "base"})

    assert response.status_code == 400
    assert "could not extract readable text from the provided url." in response.text.lower()
