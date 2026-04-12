from __future__ import annotations

from html import escape

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

from seminar_compass.models import InputType, OutputType, ReconstructionRequest
from seminar_compass.pipeline import SeminarCompassPipeline

app = FastAPI(title="Seminar Compass MVP")
pipeline = SeminarCompassPipeline()


@app.get("/", response_class=HTMLResponse)
def raw_text_input_page() -> str:
    return """
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
      <textarea id=\"content\" name=\"content\" rows=\"16\" cols=\"100\" required></textarea><br />
      <button type=\"submit\">Reconstruct</button>
    </form>
  </body>
</html>
"""


def _list_html(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


@app.post("/raw-text", response_class=HTMLResponse)
def raw_text_result_page(content: str = Form(...)) -> str:
    response = pipeline.reconstruct(
        ReconstructionRequest(input_type=InputType.RAW_TEXT, content=content)
    )
    base_output = next(
        output for output in response.primary_outputs if output.output_type == OutputType.BASE
    )

    supplemental = (
        f"<p>{escape(base_output.supplemental_explanation)}</p>"
        if base_output.supplemental_explanation
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

    <h2>Top 3 takeaways</h2>
    {_list_html(base_output.top_takeaways)}

    <h2>Main claim</h2>
    <p>{escape(base_output.main_claim)}</p>

    <h2>Conditions / assumptions</h2>
    {_list_html(base_output.conditions_assumptions)}

    <h2>Practical takeaway</h2>
    <p>{escape(base_output.practical_takeaway)}</p>

    <h2>Prerequisite knowledge</h2>
    {_list_html(base_output.prerequisite_knowledge)}

    <h2>What to consume first</h2>
    {_list_html(base_output.what_to_watch_read_first)}

    <h2>Safely skippable parts</h2>
    {_list_html(base_output.safely_skippable_parts)}

    <h2>Original-order summary</h2>
    <p>{escape(base_output.original_order_summary)}</p>

    <h2>Reconstructed summary</h2>
    <p>{escape(base_output.reconstructed_summary)}</p>

    <h2>3-line reactivation summary</h2>
    {_list_html(base_output.reactivation_3line)}

    <h2>Retrieval questions</h2>
    {_list_html(base_output.retrieval_questions)}

    <h2>Confidence note</h2>
    <p>{escape(base_output.confidence_note)}</p>

    <h2>Supplemental explanation (separate)</h2>
    {supplemental}
  </body>
</html>
"""
