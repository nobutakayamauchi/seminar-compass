from __future__ import annotations

from html import escape

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

from seminar_compass.models import InputType, OutputType, ReconstructionRequest
from seminar_compass.pipeline import SeminarCompassPipeline

app = FastAPI(title="Seminar Compass MVP")
pipeline = SeminarCompassPipeline()

EXAMPLE_RAW_TEXT = (
    "The main claim is that short daily retrieval improves long-term retention. "
    "If the material is new or dense, first do a 2-minute preview before deep study. "
    "Example: after a seminar, write three recall bullets and one next action."
)

MODE_HELP = {
    OutputType.BASE: "Faithful structured extraction from primary source content.",
    OutputType.PREVIEW: "Fast orientation before full consumption.",
    OutputType.REVIEW: "Retrieval-focused prompts for reactivation.",
    OutputType.EASIER: "Simpler phrasing without changing facts.",
}

MODE_WHEN_TO_USE = {
    OutputType.BASE: "Use when you need the standard full reconstruction first.",
    OutputType.PREVIEW: "Use before committing time to the full source.",
    OutputType.REVIEW: "Use after first pass to strengthen recall and next action.",
    OutputType.EASIER: "Use when wording feels too dense and you need a simpler pass.",
}


@app.get("/", response_class=HTMLResponse)
def raw_text_input_page() -> str:
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
    <section>
      <h2>Internal beta scope</h2>
      <p><strong>Stable primary path:</strong> raw-text reconstruction via this form.</p>
      <p><strong>Supported now:</strong> raw text, simple URL-to-text extraction, mode comparison, support-material separation.</p>
      <p><strong>Not supported yet:</strong> embedded-video handling, media transcription, advanced ingestion.</p>
    </section>
    <form method=\"post\" action=\"/raw-text\">
      <label for=\"content\">Paste raw text</label><br />
      <textarea id=\"content\" name=\"content\" rows=\"16\" cols=\"100\" required>{escape(EXAMPLE_RAW_TEXT)}</textarea><br />
      <p><small>Quick start: edit this example text, then click Reconstruct.</small></p>

      <label for=\"support_materials\">Optional support material (separate from primary outputs)</label><br />
      <textarea id=\"support_materials\" name=\"support_materials\" rows=\"6\" cols=\"100\" placeholder=\"Optional: paste support notes or references. Use a line with --- to separate multiple supports.\"></textarea><br />
      <p><small>Guidance: support material is used only for supplemental explanation and kept separate from primary reconstruction output.</small></p>

      <button type=\"submit\">Reconstruct</button>
    </form>
  </body>
</html>
"""


def _list_html(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def _parse_support_materials(raw: str | None) -> list[str]:
    if raw is None:
        return []

    chunks = [chunk.strip() for chunk in raw.split("\n---\n")]
    return [chunk for chunk in chunks if chunk]


@app.post("/raw-text", response_class=HTMLResponse)
def raw_text_result_page(
    content: str = Form(...), support_materials: str | None = Form(default=None)
) -> str:
    response = pipeline.reconstruct(
        ReconstructionRequest(
            input_type=InputType.RAW_TEXT,
            content=content,
            support_materials=_parse_support_materials(support_materials),
        )
    )

    output_by_type = {output.output_type: output for output in response.primary_outputs}
    base_output = output_by_type[OutputType.BASE]

    supplemental = (
        f"<p>{escape(base_output.supplemental_explanation)}</p>"
        if base_output.supplemental_explanation
        else "<p>None provided.</p>"
    )

    mode_rows = "".join(
        (
            "<tr>"
            f"<td><strong>{escape(mode.value)}</strong></td>"
            f"<td>{escape(MODE_HELP[mode])}</td>"
            f"<td>{escape(MODE_WHEN_TO_USE[mode])}</td>"
            f"<td>{escape(output_by_type[mode].reconstructed_summary)}</td>"
            "</tr>"
        )
        for mode in [OutputType.BASE, OutputType.PREVIEW, OutputType.REVIEW, OutputType.EASIER]
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

    <h2>Mode differences (quick view)</h2>
    <table border="1" cellpadding="6" cellspacing="0">
      <thead>
        <tr>
          <th>Mode</th>
          <th>What it is</th>
          <th>When to use</th>
          <th>Summary output</th>
        </tr>
      </thead>
      <tbody>{mode_rows}</tbody>
    </table>

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
