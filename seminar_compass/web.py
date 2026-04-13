from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from uuid import uuid4

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse

from seminar_compass.models import InputType, OutputType, ReconstructionRequest, ReconstructionResponse
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


@dataclass
class SavedResult:
    id: str
    created_at: str
    title: str | None
    note: str | None
    input_type: InputType
    selected_mode: OutputType
    response: ReconstructionResponse


@dataclass
class HistoryItem:
    id: str
    created_at: str
    title: str | None
    note: str | None
    input_type: InputType
    selected_mode: OutputType
    main_claim: str
    result_ref: str


RESULTS_BY_ID: dict[str, SavedResult] = {}
RESULT_HISTORY: list[HistoryItem] = []


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
    <p><a href=\"/history\">View saved history</a></p>
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

      <label for=\"title\">Optional title</label><br />
      <input id=\"title\" name=\"title\" type=\"text\" maxlength=\"120\" /><br />

      <label for=\"note\">Optional one-line note</label><br />
      <input id=\"note\" name=\"note\" type=\"text\" maxlength=\"240\" /><br />

      <label for=\"selected_mode\">Selected mode</label><br />
      <select id=\"selected_mode\" name=\"selected_mode\">
        <option value=\"base\">base</option>
        <option value=\"preview\">preview</option>
        <option value=\"review\">review</option>
        <option value=\"easier\">easier</option>
      </select><br />

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


def _parse_mode(selected_mode: str | None) -> OutputType:
    if not selected_mode:
        return OutputType.BASE

    try:
        return OutputType(selected_mode)
    except ValueError:
        return OutputType.BASE


def _render_result_page(saved: SavedResult) -> str:
    output_by_type = {output.output_type: output for output in saved.response.primary_outputs}
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

    saved_title = saved.title if saved.title else "(none)"
    saved_note = saved.note if saved.note else "(none)"

    return f"""
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <title>Seminar Compass Result (MVP)</title>
  </head>
  <body>
    <h1>Reconstruction Result</h1>
    <p><a href=\"/\">← Back to input</a> | <a href=\"/history\">View saved history</a></p>

    <h2>Saved history metadata</h2>
    <p><strong>Saved history item ID:</strong> {escape(saved.id)}</p>
    <p><strong>Created at:</strong> {escape(saved.created_at)}</p>
    <p><strong>Input type:</strong> {escape(saved.input_type.value)}</p>
    <p><strong>Selected mode for this run:</strong> {escape(saved.selected_mode.value)}</p>
    <p><strong>Title:</strong> {escape(saved_title)}</p>
    <p><strong>Note:</strong> {escape(saved_note)}</p>

    <h2>Mode differences (quick view)</h2>
    <table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">
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


@app.post("/raw-text", response_class=HTMLResponse)
def raw_text_result_page(
    content: str = Form(...),
    support_materials: str | None = Form(default=None),
    title: str | None = Form(default=None),
    note: str | None = Form(default=None),
    selected_mode: str | None = Form(default=None),
) -> str:
    response = pipeline.reconstruct(
        ReconstructionRequest(
            input_type=InputType.RAW_TEXT,
            content=content,
            support_materials=_parse_support_materials(support_materials),
        )
    )

    chosen_mode = _parse_mode(selected_mode)
    output_by_type = {output.output_type: output for output in response.primary_outputs}

    saved_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    normalized_title = title.strip() if title and title.strip() else None
    normalized_note = note.strip() if note and note.strip() else None

    saved = SavedResult(
        id=saved_id,
        created_at=created_at,
        title=normalized_title,
        note=normalized_note,
        input_type=InputType.RAW_TEXT,
        selected_mode=chosen_mode,
        response=response,
    )
    RESULTS_BY_ID[saved_id] = saved

    RESULT_HISTORY.insert(
        0,
        HistoryItem(
            id=saved_id,
            created_at=created_at,
            title=normalized_title,
            note=normalized_note,
            input_type=InputType.RAW_TEXT,
            selected_mode=chosen_mode,
            main_claim=output_by_type[chosen_mode].main_claim,
            result_ref=saved_id,
        ),
    )

    return _render_result_page(saved)


@app.get("/history", response_class=HTMLResponse)
def history_page() -> str:
    if not RESULT_HISTORY:
        items_html = "<p>No saved items yet.</p>"
    else:
        items_html = "<ul>" + "".join(
            (
                "<li>"
                f"<a href=\"/history/{escape(item.id)}\">{escape(item.title or item.id)}</a>"
                f" — {escape(item.created_at)}"
                f" — mode: {escape(item.selected_mode.value)}"
                f" — input: {escape(item.input_type.value)}"
                f" — note: {escape(item.note or '(none)')}"
                f"<br /><small>Main claim: {escape(item.main_claim)}</small>"
                "</li>"
            )
            for item in RESULT_HISTORY
        ) + "</ul>"

    return f"""
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <title>Seminar Compass History (MVP)</title>
  </head>
  <body>
    <h1>Saved history</h1>
    <p><a href=\"/\">← Back to input</a></p>
    {items_html}
  </body>
</html>
"""


@app.get("/history/{item_id}", response_class=HTMLResponse)
def history_item_page(item_id: str) -> str:
    saved = RESULTS_BY_ID.get(item_id)
    if saved is None:
        raise HTTPException(status_code=404, detail="History item not found")

    return _render_result_page(saved)
