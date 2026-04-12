from __future__ import annotations

from html import escape
from html.parser import HTMLParser
import re
from urllib.parse import urlparse
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

from seminar_compass.models import InputType, OutputType, ReconstructionRequest
from seminar_compass.pipeline import SeminarCompassPipeline

app = FastAPI(title="Seminar Compass MVP")
pipeline = SeminarCompassPipeline()
MODE_OPTIONS = [OutputType.BASE, OutputType.PREVIEW, OutputType.REVIEW, OutputType.EASIER]


class _ReadableTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:  # noqa: ARG002
        if tag in {"script", "style", "noscript"}:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = False
        if tag in {"p", "li", "div", "section", "article", "br"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip and data.strip():
            self.parts.append(data.strip())


@app.get("/", response_class=HTMLResponse)
def raw_text_input_page() -> str:
    options = "".join(
        f'<option value="{mode.value}">{escape(mode.value)}</option>' for mode in MODE_OPTIONS
    )
    return f"""
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <title>Seminar Compass (MVP)</title>
  </head>
  <body>
    <h1>Seminar Compass</h1>
    <p>Raw-text reconstruction MVP.</p>
    <form method=\"post\" action=\"/raw-text\">
      <label for=\"content\">Paste raw text</label><br />
      <textarea id=\"content\" name=\"content\" rows=\"14\" cols=\"100\" required placeholder=\"Paste source text here...\"></textarea><br />
      <small>Tip: include enough text for meaningful extraction (not just a title).</small><br /><br />

      <label for=\"mode\">Mode</label><br />
      <select id=\"mode\" name=\"mode\">{options}</select><br />
      <small>Modes: base (default), preview, review, easier.</small><br /><br />

      <label for=\"support_materials\">Support materials (optional)</label><br />
      <textarea id=\"support_materials\" name=\"support_materials\" rows=\"6\" cols=\"100\" placeholder=\"Add optional context. Separate multiple items with a blank line.\"></textarea><br />

      <button type=\"submit\">Reconstruct</button>
    </form>

    <hr />

    <h2>URL input (minimal)</h2>
    <form method=\"post\" action=\"/url\">
      <label for=\"url\">URL</label><br />
      <input id=\"url\" name=\"url\" type=\"url\" size=\"100\" required placeholder=\"https://example.com/article\" /><br />
      <small>Simple HTML pages only for this MVP step.</small><br /><br />

      <label for=\"mode_url\">Mode</label><br />
      <select id=\"mode_url\" name=\"mode\">{options}</select><br />
      <small>Modes: base (default), preview, review, easier.</small><br /><br />

      <label for=\"support_materials_url\">Support materials (optional)</label><br />
      <textarea id=\"support_materials_url\" name=\"support_materials\" rows=\"6\" cols=\"100\" placeholder=\"Add optional context. Separate multiple items with a blank line.\"></textarea><br />

      <button type=\"submit\">Extract and reconstruct</button>
    </form>
  </body>
</html>
"""


def _list_html(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def _parse_support_materials(support_materials: str) -> list[str]:
    if not support_materials.strip():
        return []
    return [chunk.strip() for chunk in re.split(r"\n\s*\n+", support_materials) if chunk.strip()]


def _extract_readable_text(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Please enter a valid http(s) URL.")

    try:
        with urlopen(url.strip(), timeout=8) as response:
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type.lower():
                raise ValueError("Could not extract readable text from the provided URL.")
            html = response.read(300_000).decode("utf-8", errors="ignore")
    except (URLError, ValueError, TimeoutError, UnicodeDecodeError):
        raise ValueError("Could not extract readable text from the provided URL.")

    parser = _ReadableTextParser()
    parser.feed(html)
    text = re.sub(r"\n\s*\n+", "\n\n", "\n".join(parser.parts))
    text = re.sub(r"[ \t]+", " ", text).strip()
    if len(text) < 40:
        raise ValueError("Could not extract readable text from the provided URL.")
    return text


def _build_result_page(content: str, mode: str, support_materials: str) -> str:
    response = pipeline.reconstruct(
        ReconstructionRequest(
            input_type=InputType.RAW_TEXT,
            content=content,
            support_materials=_parse_support_materials(support_materials),
        )
    )

    selected_output_type = OutputType(mode) if mode in {m.value for m in MODE_OPTIONS} else OutputType.BASE
    selected_output = next(
        output
        for output in response.primary_outputs
        if output.output_type == selected_output_type
    )

    supplemental = (
        f"<p>{escape(selected_output.supplemental_explanation)}</p>"
        if selected_output.supplemental_explanation
        else "<p>None provided.</p>"
    )
    mode_list = ", ".join(
        f"{m.value}{' (selected)' if m == selected_output.output_type else ''}" for m in MODE_OPTIONS
    )

    return f"""
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <title>Seminar Compass Result (MVP)</title>
  </head>
  <body>
    <h1>Reconstruction Result</h1>
    <p><a href=\"/\">← Back to input</a></p>
    <p><strong>Selected mode:</strong> {escape(selected_output.output_type.value)}</p>
    <p><strong>Available modes:</strong> {escape(mode_list)}</p>
    <hr />

    <section>
      <h2>Core outputs</h2>

      <h3>Top 3 takeaways</h3>
      {_list_html(selected_output.top_takeaways)}

      <h3>Main claim</h3>
      <p>{escape(selected_output.main_claim)}</p>

      <h3>Conditions / assumptions</h3>
      {_list_html(selected_output.conditions_assumptions)}

      <h3>Practical takeaway</h3>
      <p>{escape(selected_output.practical_takeaway)}</p>

      <h3>Prerequisite knowledge</h3>
      {_list_html(selected_output.prerequisite_knowledge)}

      <h3>What to consume first</h3>
      {_list_html(selected_output.what_to_watch_read_first)}

      <h3>Safely skippable parts</h3>
      {_list_html(selected_output.safely_skippable_parts)}

      <h3>Original-order summary</h3>
      <p>{escape(selected_output.original_order_summary)}</p>

      <h3>Reconstructed summary</h3>
      <p>{escape(selected_output.reconstructed_summary)}</p>

      <h3>3-line reactivation summary</h3>
      {_list_html(selected_output.reactivation_3line)}

      <h3>Retrieval questions</h3>
      {_list_html(selected_output.retrieval_questions)}

      <h3>Confidence note</h3>
      <p>{escape(selected_output.confidence_note)}</p>
    </section>

    <hr />
    <section>
      <h2>Supplemental explanation (separate)</h2>
      {supplemental}
    </section>
  </body>
</html>
"""


@app.post("/raw-text", response_class=HTMLResponse)
def raw_text_result_page(
    content: str = Form(...),
    mode: str = Form(OutputType.BASE.value),
    support_materials: str = Form(""),
) -> str:
    if not content.strip():
        return HTMLResponse(
            """
<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\" /><title>Input Error</title></head>
<body>
  <h1>Input required</h1>
  <p>Please paste raw text before submitting.</p>
  <p><a href=\"/\">← Back to input</a></p>
</body></html>
""",
            status_code=400,
        )
    return _build_result_page(content, mode, support_materials)


@app.post("/url", response_class=HTMLResponse)
def url_result_page(
    url: str = Form(...),
    mode: str = Form(OutputType.BASE.value),
    support_materials: str = Form(""),
):
    try:
        content = _extract_readable_text(url)
    except ValueError as exc:
        message = escape(str(exc) or "Could not extract readable text from the provided URL.")
        return HTMLResponse(
            f"""
<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\" /><title>Extraction Error</title></head>
<body>
  <h1>URL extraction failed</h1>
  <p>{message}</p>
  <p><a href=\"/\">← Back to input</a></p>
</body></html>
""",
            status_code=400,
        )

    return _build_result_page(content, mode, support_materials)
