from __future__ import annotations

from html import escape
from html.parser import HTMLParser
import re
from urllib.error import URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

from seminar_compass.models import InputType, OutputType, ReconstructionOutput, ReconstructionRequest
from seminar_compass.pipeline import SeminarCompassPipeline

app = FastAPI(title="Seminar Compass MVP")
pipeline = SeminarCompassPipeline()
MODE_OPTIONS = [OutputType.BASE, OutputType.PREVIEW, OutputType.REVIEW, OutputType.EASIER]


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag in {"p", "div", "section", "article", "li", "h1", "h2", "h3", "br"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and data.strip():
            self.parts.append(data.strip())


def _list_html(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def _parse_support_materials(support_materials: str) -> list[str]:
    if not support_materials.strip():
        return []
    return [chunk.strip() for chunk in re.split(r"\n\s*\n+", support_materials) if chunk.strip()]


def _extract_text_from_url(url: str) -> str:
    req = Request(url.strip(), headers={"User-Agent": "seminar-compass-mvp/1.0"})
    try:
        with urlopen(req, timeout=8) as response:
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type.lower():
                raise ValueError("URL did not return an HTML page.")
            html = response.read(300_000).decode("utf-8", errors="ignore")
    except (URLError, ValueError, TimeoutError):
        raise ValueError("Could not extract readable text from the provided URL.")

    parser = _VisibleTextParser()
    parser.feed(html)
    text = re.sub(r"\n\s*\n+", "\n\n", "\n".join(parser.parts))
    text = re.sub(r"[ \t]+", " ", text).strip()
    if len(text) < 40:
        raise ValueError("Could not extract readable text from the provided URL.")
    return text


def _render_output_page(selected_output: ReconstructionOutput) -> str:
    supplemental = (
        f"<p>{escape(selected_output.supplemental_explanation)}</p>"
        if selected_output.supplemental_explanation
        else "<p>None provided.</p>"
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
    <hr />

    <section>
      <h2>Top 3 takeaways</h2>
      {_list_html(selected_output.top_takeaways)}
      <h2>Main claim</h2>
      <p>{escape(selected_output.main_claim)}</p>
      <h2>Conditions / assumptions</h2>
      {_list_html(selected_output.conditions_assumptions)}
      <h2>Practical takeaway</h2>
      <p>{escape(selected_output.practical_takeaway)}</p>
      <h2>Prerequisite knowledge</h2>
      {_list_html(selected_output.prerequisite_knowledge)}
      <h2>What to consume first</h2>
      {_list_html(selected_output.what_to_watch_read_first)}
      <h2>Safely skippable parts</h2>
      {_list_html(selected_output.safely_skippable_parts)}
      <h2>Original-order summary</h2>
      <p>{escape(selected_output.original_order_summary)}</p>
      <h2>Reconstructed summary</h2>
      <p>{escape(selected_output.reconstructed_summary)}</p>
      <h2>3-line reactivation summary</h2>
      {_list_html(selected_output.reactivation_3line)}
      <h2>Retrieval questions</h2>
      {_list_html(selected_output.retrieval_questions)}
      <h2>Confidence note</h2>
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


def _run_reconstruction(content: str, mode: str, support_materials: str) -> ReconstructionOutput:
    response = pipeline.reconstruct(
        ReconstructionRequest(
            input_type=InputType.RAW_TEXT,
            content=content,
            support_materials=_parse_support_materials(support_materials),
        )
    )
    selected_output_type = OutputType(mode) if mode in {m.value for m in MODE_OPTIONS} else OutputType.BASE
    return next(
        output
        for output in response.primary_outputs
        if output.output_type == selected_output_type
    )


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
    <p>Raw-text reconstruction MVP with minimal URL ingestion.</p>

    <h2>Raw text input (stable path)</h2>
    <form method=\"post\" action=\"/raw-text\">
      <label for=\"content\">Paste raw text</label><br />
      <textarea id=\"content\" name=\"content\" rows=\"14\" cols=\"100\" required></textarea><br /><br />
      <label for=\"mode\">Mode</label><br />
      <select id=\"mode\" name=\"mode\">{options}</select><br /><br />
      <label for=\"support_materials\">Support materials (optional, separate entries with blank lines)</label><br />
      <textarea id=\"support_materials\" name=\"support_materials\" rows=\"6\" cols=\"100\"></textarea><br />
      <button type=\"submit\">Reconstruct from raw text</button>
    </form>

    <hr />

    <h2>URL input (minimal)</h2>
    <form method=\"post\" action=\"/url\">
      <label for=\"url\">URL</label><br />
      <input id=\"url\" name=\"url\" type=\"url\" size=\"100\" required /><br /><br />
      <label for=\"mode_url\">Mode</label><br />
      <select id=\"mode_url\" name=\"mode\">{options}</select><br /><br />
      <label for=\"support_materials_url\">Support materials (optional, separate entries with blank lines)</label><br />
      <textarea id=\"support_materials_url\" name=\"support_materials\" rows=\"6\" cols=\"100\"></textarea><br />
      <button type=\"submit\">Extract and reconstruct</button>
    </form>
  </body>
</html>
"""


@app.post("/raw-text", response_class=HTMLResponse)
def raw_text_result_page(
    content: str = Form(...),
    mode: str = Form(OutputType.BASE.value),
    support_materials: str = Form(""),
) -> str:
    return _render_output_page(_run_reconstruction(content, mode, support_materials))


@app.post("/url", response_class=HTMLResponse)
def url_result_page(
    url: str = Form(...),
    mode: str = Form(OutputType.BASE.value),
    support_materials: str = Form(""),
):
    try:
        extracted_text = _extract_text_from_url(url)
    except ValueError:
        return HTMLResponse(
            """
<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\" /><title>Extraction Error</title></head>
<body>
  <h1>URL extraction failed</h1>
  <p>Could not extract readable text from the provided URL.</p>
  <p><a href=\"/\">← Back to input</a></p>
</body></html>
""",
            status_code=400,
        )

    return _render_output_page(_run_reconstruction(extracted_text, mode, support_materials))
