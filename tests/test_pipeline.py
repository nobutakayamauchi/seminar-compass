from seminar_compass import InputType, ReconstructionRequest, SeminarCompassPipeline
from seminar_compass.models import OutputType, SourceKind


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
