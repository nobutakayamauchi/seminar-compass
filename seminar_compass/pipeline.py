from __future__ import annotations

from dataclasses import replace
import re
import uuid
from typing import Iterable, List

from seminar_compass.models import (
    EvidenceReference,
    InputType,
    OutputType,
    ReconstructionOutput,
    ReconstructionRequest,
    ReconstructionResponse,
    SourceDocument,
    SourceKind,
    SourceRole,
    SourceSegment,
)


class SeminarCompassPipeline:
    """MVP reconstruction pipeline.

    Design constraints:
    - No unsupported factual supplementation.
    - No uncertain inference presented as fact.
    - Preserve claim/condition linkage.
    - Keep primary summary separate from support-material explanation.
    """

    def reconstruct(self, request: ReconstructionRequest) -> ReconstructionResponse:
        primary_doc = self._build_primary_doc(request)
        support_docs = self._build_support_docs(request.support_materials)
        primary_segments = self._segment(primary_doc)

        base_output = self._build_base_output(primary_segments)
        outputs = [
            base_output,
            self._build_preview_output(base_output),
            self._build_review_output(base_output),
            self._build_easier_output(base_output),
        ]

        if support_docs:
            support_summary = self._build_support_explanation(support_docs)
            for output in outputs:
                output.supplemental_explanation = support_summary

        return ReconstructionResponse(
            primary_outputs=outputs,
            materials_used=[doc.title or doc.id for doc in support_docs],
        )

    def _build_primary_doc(self, request: ReconstructionRequest) -> SourceDocument:
        kind = {
            InputType.URL: SourceKind.URL_TEXT,
            InputType.RAW_TEXT: SourceKind.RAW_TEXT,
            InputType.MEDIA_UPLOAD: SourceKind.TRANSCRIPT,
        }[request.input_type]

        cleaned = self._clean_text(request.content)
        return SourceDocument(
            id=f"src_{uuid.uuid4().hex[:8]}",
            role=SourceRole.PRIMARY,
            source_kind=kind,
            title=None,
            normalized_text=cleaned,
        )

    def _build_support_docs(self, supports: Iterable[str]) -> List[SourceDocument]:
        docs: List[SourceDocument] = []
        for idx, text in enumerate(supports):
            cleaned = self._clean_text(text)
            docs.append(
                SourceDocument(
                    id=f"sup_{uuid.uuid4().hex[:8]}",
                    role=SourceRole.SUPPORT,
                    source_kind=SourceKind.UPLOADED_SUPPORT,
                    title=f"support_{idx + 1}",
                    normalized_text=cleaned,
                )
            )
        return docs

    def _segment(self, document: SourceDocument) -> List[SourceSegment]:
        paragraphs = [p.strip() for p in document.normalized_text.split("\n") if p.strip()]
        if not paragraphs:
            paragraphs = [document.normalized_text]
        segments = []
        for i, paragraph in enumerate(paragraphs, start=1):
            segments.append(
                SourceSegment(
                    id=f"seg_{uuid.uuid4().hex[:8]}",
                    source_document_id=document.id,
                    text=paragraph,
                    segment_index=i,
                    paragraph_start=i,
                    paragraph_end=i,
                )
            )
        return segments

    def _build_base_output(self, segments: List[SourceSegment]) -> ReconstructionOutput:
        joined = " ".join(segment.text for segment in segments)
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", joined) if s.strip()]
        if not sentences:
            sentences = ["No sufficient primary-content evidence was found."]

        top_takeaways = self._build_top_takeaways(sentences)
        claim = self._bounded_text(
            lambda: sentences[0],
            self.MAIN_CLAIM_CAP,
            "Main claim could not be isolated cleanly.",
        )
        conditions = self._extract_conditions(sentences)
        practical = self._bounded_text(
            lambda: (sentences[1] if len(sentences) > 1 else claim),
            self.PRACTICAL_TAKEAWAY_ITEM_CAP,
            "Practical takeaway could not be compressed cleanly.",
        )

        refs = [
            EvidenceReference(
                output_field="main_claim",
                source_segment_id=segments[0].id,
                role=SourceRole.PRIMARY,
            )
        ] if segments else []

        confidence_note = (
            "High confidence in extraction from explicit source text."
            if len(sentences) >= 3
            else "Limited evidence; output may be incomplete."
        )

        return ReconstructionOutput(
            output_type=OutputType.BASE,
            top_takeaways=top_takeaways,
            main_claim=claim,
            conditions_assumptions=conditions,
            practical_takeaway=practical,
            prerequisite_knowledge=self._extract_prerequisites(joined),
            what_to_watch_read_first=[
                self._bounded_text(
                    lambda: claim,
                    self.WHAT_TO_CONSUME_FIRST_CAP,
                    "What to consume first could not be isolated cleanly.",
                )
            ],
            safely_skippable_parts=self._extract_skippable(sentences),
            original_order_summary=" ".join(sentences[:5]),
            reconstructed_summary=self._reconstruct(sentences),
            reactivation_3line=top_takeaways,
            retrieval_questions=self._retrieval_questions(claim),
            confidence_note=confidence_note,
            source_references=refs,
        )

    def _build_preview_output(self, base: ReconstructionOutput) -> ReconstructionOutput:
        preview_summary = self._bounded_text(
            lambda: f"Preview: {base.main_claim}",
            self.PREVIEW_CAP,
            "Preview could not be compressed cleanly.",
        )
        return replace(
            base,
            output_type=OutputType.PREVIEW,
            reconstructed_summary=preview_summary,
            retrieval_questions=base.retrieval_questions[:2],
        )

    def _build_review_output(self, base: ReconstructionOutput) -> ReconstructionOutput:
        return replace(
            base,
            output_type=OutputType.REVIEW,
            reconstructed_summary="Review mode: recall key claim, condition, and next action.",
            retrieval_questions=base.retrieval_questions
            + [
                "Restate the main claim in one sentence.",
                "What is your next action?",
            ],
        )

    def _build_easier_output(self, base: ReconstructionOutput) -> ReconstructionOutput:
        return replace(
            base,
            output_type=OutputType.EASIER,
            reconstructed_summary=f"In simple terms: {base.main_claim}",
        )

    @staticmethod
    def _build_support_explanation(support_docs: List[SourceDocument]) -> str:
        snippets = [doc.normalized_text[:180] for doc in support_docs if doc.normalized_text]
        if not snippets:
            return "Support materials were provided, but evidence was insufficient."
        return "Supplemental explanation (separate from primary summary): " + " | ".join(snippets)

    @staticmethod
    def _clean_text(text: str) -> str:
        paragraphs = re.split(r"\n\s*\n+", text.strip())
        cleaned = [re.sub(r"\s+", " ", p).strip() for p in paragraphs if p.strip()]
        return "\n".join(cleaned)

    @staticmethod
    def _extract_conditions(sentences: List[str]) -> List[str]:
        conditions = [s for s in sentences if any(token in s.lower() for token in ["if ", "when ", "unless ", "assuming "])]
        return conditions or ["No explicit condition detected in source text."]

    @staticmethod
    def _extract_prerequisites(text: str) -> List[str]:
        markers = []
        lower = text.lower()
        if "prerequisite" in lower:
            markers.append("The source explicitly mentions prerequisites.")
        if "basics" in lower or "fundamentals" in lower:
            markers.append("Basic/fundamental prior knowledge is referenced.")
        return markers or ["No explicit prerequisites detected; verify with full source."]

    @staticmethod
    def _extract_skippable(sentences: List[str]) -> List[str]:
        skippable = [s for s in sentences if "example" in s.lower() or "anecdote" in s.lower()]
        return skippable[:3] or ["No safely skippable part identified with high confidence."]

    @staticmethod
    def _reconstruct(sentences: List[str]) -> str:
        if len(sentences) <= 2:
            return " ".join(sentences)
        return f"Priority first: {sentences[0]} Then conditions: {sentences[1]} Finally action: {sentences[-1]}"

    @staticmethod
    def _retrieval_questions(main_claim: str) -> List[str]:
        return [
            "What is the main claim?",
            "Under what conditions does the claim hold?",
            f"How would you apply this claim: '{main_claim[:100]}'?",
        ]

    def _build_top_takeaways(self, sentences: List[str]) -> List[str]:
        takeaways: List[str] = []
        for sentence in sentences:
            trimmed = self._trim_to_two_sentences(sentence)
            if not trimmed:
                continue
            compact = self._bounded_text(
                lambda value=trimmed: value,
                self.TAKEAWAY_ITEM_CAP,
                "Takeaway could not be compressed cleanly.",
            )
            if compact not in takeaways:
                takeaways.append(compact)
            if len(takeaways) == 3:
                break
        return takeaways or ["Takeaway could not be compressed cleanly."]

    @staticmethod
    def _trim_to_two_sentences(text: str) -> str:
        sentence_parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        if sentence_parts:
            return " ".join(sentence_parts[:2])
        return text.strip()

    @staticmethod
    def _apply_cap(text: str, cap: int) -> str:
        if len(text) <= cap:
            return text
        return text[:cap].rstrip()

    def _bounded_text(
        self, generate_fn, cap: int, fallback: str
    ) -> str:
        generated = generate_fn() or ""
        if not generated.strip():
            return fallback if len(fallback) <= cap else self._apply_cap(fallback, cap)
        if len(generated) <= cap:
            return generated

        repaired = self._repair_short(generated, cap)
        if len(repaired) <= cap:
            return repaired

        if len(fallback) <= cap:
            return fallback

        return self._apply_cap(repaired, cap)

    @staticmethod
    def _repair_short(text: str, cap: int) -> str:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        if sentences:
            candidate = sentences[0]
            if len(candidate) <= cap:
                return candidate
        return SeminarCompassPipeline._apply_cap(text, cap)
    PREVIEW_CAP = 280
    MAIN_CLAIM_CAP = 140
    WHAT_TO_CONSUME_FIRST_CAP = 120
    TAKEAWAY_ITEM_CAP = 80
    PRACTICAL_TAKEAWAY_ITEM_CAP = 60
