from seminar_compass import InputType, ReconstructionRequest, SeminarCompassPipeline
from seminar_compass.models import EvidenceReference, OutputType, SourceKind


def test_reconstruction_generates_expected_output_types():
    pipeline = SeminarCompassPipeline()
    request = ReconstructionRequest(
        input_type=InputType.RAW_TEXT,
        content="Main claim. If condition applies, do action. Example details.",
        support_materials=["Support document about context."],
    )

    response = pipeline.reconstruct(request)
    kinds = {out.output_type for out in response.primary_outputs}

    assert kinds == {OutputType.BASE, OutputType.PREVIEW, OutputType.REVIEW, OutputType.EASIER}
    assert response.materials_used == ["support_1"]
    assert all(out.supplemental_explanation for out in response.primary_outputs)


def test_primary_source_kind_tracks_input_type():
    pipeline = SeminarCompassPipeline()

    request = ReconstructionRequest(
        input_type=InputType.MEDIA_UPLOAD,
        content="Transcript content sentence one. sentence two.",
    )

    doc = pipeline._build_primary_doc(request)
    assert doc.source_kind == SourceKind.TRANSCRIPT


def test_derived_outputs_keep_evidence_reference_type():
    pipeline = SeminarCompassPipeline()
    request = ReconstructionRequest(
        input_type=InputType.RAW_TEXT,
        content="Main claim. Supporting detail.",
    )

    response = pipeline.reconstruct(request)
    for output in response.primary_outputs:
        assert output.source_references
        assert isinstance(output.source_references[0], EvidenceReference)


def test_clean_text_preserves_paragraph_breaks():
    pipeline = SeminarCompassPipeline()

    cleaned = pipeline._clean_text("One line.\ncontinued.\n\nSecond paragraph.\n\n\nThird paragraph.")

    assert cleaned == "One line. continued.\nSecond paragraph.\nThird paragraph."


def test_output_fields_are_capped_for_long_source_text():
    pipeline = SeminarCompassPipeline()
    long_sentence = "A" * 400 + "."
    request = ReconstructionRequest(
        input_type=InputType.RAW_TEXT,
        content=f"{long_sentence} {long_sentence} {long_sentence}",
    )

    response = pipeline.reconstruct(request)
    base = next(out for out in response.primary_outputs if out.output_type == OutputType.BASE)
    preview = next(out for out in response.primary_outputs if out.output_type == OutputType.PREVIEW)

    assert len(base.main_claim) <= pipeline.MAIN_CLAIM_CAP
    assert all(len(item) <= pipeline.TAKEAWAY_ITEM_CAP for item in base.top_takeaways)
    assert all(
        len(item) <= pipeline.WHAT_TO_CONSUME_FIRST_CAP for item in base.what_to_watch_read_first
    )
    assert len(base.practical_takeaway) <= pipeline.PRACTICAL_TAKEAWAY_ITEM_CAP
    assert len(preview.reconstructed_summary) <= pipeline.PREVIEW_CAP


def test_bounded_text_uses_short_fallback_when_needed():
    pipeline = SeminarCompassPipeline()
    capped = pipeline._bounded_text(
        lambda: "X" * 500,
        cap=20,
        fallback="Main claim could not be isolated cleanly.",
    )

    assert capped == "XXXXXXXXXXXXXXXXXXXX"
