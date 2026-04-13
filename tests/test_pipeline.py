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


def test_main_claim_is_limited_to_three_sentences():
    pipeline = SeminarCompassPipeline()
    request = ReconstructionRequest(
        input_type=InputType.RAW_TEXT,
        content="A first core claim. A second supporting claim. A third nuance. A fourth extra point.",
    )

    response = pipeline.reconstruct(request)
    base = next(out for out in response.primary_outputs if out.output_type == OutputType.BASE)

    assert "A first core claim." in base.main_claim
    assert "A second supporting claim." in base.main_claim
    assert "A third nuance." in base.main_claim
    assert "A fourth extra point." not in base.main_claim
    assert base.main_claim.count(".") + base.main_claim.count("!") + base.main_claim.count("?") <= 3


def test_main_claim_is_clipped_for_single_long_sentence():
    pipeline = SeminarCompassPipeline()
    request = ReconstructionRequest(
        input_type=InputType.RAW_TEXT,
        content="A" * 1000,
    )

    response = pipeline.reconstruct(request)
    base = next(out for out in response.primary_outputs if out.output_type == OutputType.BASE)

    assert len(base.main_claim) <= pipeline.MAIN_CLAIM_MAX_CHARS
