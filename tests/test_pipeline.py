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


def test_practical_takeaway_is_bounded_and_action_oriented():
    pipeline = SeminarCompassPipeline()
    request = ReconstructionRequest(
        input_type=InputType.RAW_TEXT,
        content="Core claim is important. This should be done immediately for retention and used daily. Details follow.",
    )
    response = pipeline.reconstruct(request)
    base = next(out for out in response.primary_outputs if out.output_type == OutputType.BASE)

    assert len(base.practical_takeaway) <= pipeline.PRACTICAL_MAX_CHARS
    assert base.practical_takeaway.count(".") + base.practical_takeaway.count("!") + base.practical_takeaway.count("?") <= 2


def test_top_takeaways_are_exactly_three_and_short():
    pipeline = SeminarCompassPipeline()
    request = ReconstructionRequest(
        input_type=InputType.RAW_TEXT,
        content="First concept is long and detailed. Second concept also exists. Third concept is present. Fourth should not dominate takeaways.",
    )
    response = pipeline.reconstruct(request)
    base = next(out for out in response.primary_outputs if out.output_type == OutputType.BASE)

    assert len(base.top_takeaways) == 3
    assert all(len(item) <= pipeline.TAKEAWAY_ITEM_MAX_CHARS for item in base.top_takeaways)


def test_reactivation_summary_is_three_short_lines():
    pipeline = SeminarCompassPipeline()
    request = ReconstructionRequest(
        input_type=InputType.RAW_TEXT,
        content="One claim. Two condition. Three action.",
    )
    response = pipeline.reconstruct(request)
    base = next(out for out in response.primary_outputs if out.output_type == OutputType.BASE)

    assert len(base.reactivation_3line) <= 3
    assert all(len(line) <= pipeline.REACTIVATION_LINE_MAX_CHARS for line in base.reactivation_3line)
    assert len(base.reactivation_3line) == 3


def test_final_emitted_fields_are_bounded_in_base_output():
    pipeline = SeminarCompassPipeline()
    long_block = " ".join(["Long source segment without clear breaks but with important details."] * 25)
    request = ReconstructionRequest(
        input_type=InputType.RAW_TEXT,
        content=long_block,
    )
    response = pipeline.reconstruct(request)
    base = next(out for out in response.primary_outputs if out.output_type == OutputType.BASE)

    assert len(base.main_claim) <= pipeline.MAIN_CLAIM_MAX_CHARS
    assert base.main_claim.count(".") + base.main_claim.count("!") + base.main_claim.count("?") <= 3

    assert len(base.practical_takeaway) <= pipeline.PRACTICAL_MAX_CHARS
    assert base.practical_takeaway.count(".") + base.practical_takeaway.count("!") + base.practical_takeaway.count("?") <= 2

    assert len(base.what_to_watch_read_first) == 1
    assert len(base.what_to_watch_read_first[0]) <= pipeline.WHAT_TO_CONSUME_FIRST_MAX_CHARS
    assert base.what_to_watch_read_first[0].count(".") + base.what_to_watch_read_first[0].count("!") + base.what_to_watch_read_first[0].count("?") <= 1

    assert len(base.reactivation_3line) == 3
    assert all(len(line) <= pipeline.REACTIVATION_LINE_MAX_CHARS for line in base.reactivation_3line)


def test_preview_and_easier_are_short_and_role_specific():
    pipeline = SeminarCompassPipeline()
    source = "This source begins with a long sentence that should not be replayed verbatim in preview mode. Another detail sentence appears."
    request = ReconstructionRequest(input_type=InputType.RAW_TEXT, content=source)
    response = pipeline.reconstruct(request)

    preview = next(out for out in response.primary_outputs if out.output_type == OutputType.PREVIEW)
    easier = next(out for out in response.primary_outputs if out.output_type == OutputType.EASIER)

    assert len(preview.reconstructed_summary) <= pipeline.PREVIEW_MAX_CHARS
    assert preview.reconstructed_summary.count(".") + preview.reconstructed_summary.count("!") + preview.reconstructed_summary.count("?") <= 3
    assert preview.reconstructed_summary.startswith("Preview")

    assert len(easier.reconstructed_summary) <= pipeline.EASIER_MAX_CHARS
    assert easier.reconstructed_summary.count(".") + easier.reconstructed_summary.count("!") + easier.reconstructed_summary.count("?") <= 3
    assert easier.reconstructed_summary.startswith(("In simple terms", "Simplified summary"))


def test_fallback_used_when_overflow_cannot_be_repaired():
    pipeline = SeminarCompassPipeline()
    fallback = "Main claim could not be isolated cleanly."
    result = pipeline._bounded_role_text(
        text="X" * 500,
        cap=20,
        max_sentences=3,
        fallback=fallback,
    )
    assert result == fallback[:20].rstrip()
