from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class InputType(str, Enum):
    URL = "url"
    RAW_TEXT = "raw_text"
    MEDIA_UPLOAD = "media_upload"


class SourceRole(str, Enum):
    PRIMARY = "primary"
    SUPPORT = "support"


class SourceKind(str, Enum):
    URL_TEXT = "url_text"
    RAW_TEXT = "raw_text"
    TRANSCRIPT = "transcript"
    UPLOADED_SUPPORT = "uploaded_support"
    EXTRACTED_ARTICLE = "extracted_article"


class OutputType(str, Enum):
    BASE = "base"
    PREVIEW = "preview"
    REVIEW = "review"
    EASIER = "easier"


@dataclass(slots=True)
class SourceDocument:
    id: str
    role: SourceRole
    source_kind: SourceKind
    title: Optional[str]
    normalized_text: str


@dataclass(slots=True)
class SourceSegment:
    id: str
    source_document_id: str
    text: str
    segment_index: int
    paragraph_start: Optional[int] = None
    paragraph_end: Optional[int] = None
    start_time_sec: Optional[float] = None
    end_time_sec: Optional[float] = None


@dataclass(slots=True)
class EvidenceReference:
    output_field: str
    source_segment_id: str
    role: SourceRole
    evidence_strength: str = "direct"


@dataclass(slots=True)
class ReconstructionOutput:
    output_type: OutputType
    top_takeaways: List[str]
    main_claim: str
    conditions_assumptions: List[str]
    practical_takeaway: str
    prerequisite_knowledge: List[str]
    what_to_watch_read_first: List[str]
    safely_skippable_parts: List[str]
    original_order_summary: str
    reconstructed_summary: str
    reactivation_3line: List[str]
    retrieval_questions: List[str]
    confidence_note: str
    source_references: List[EvidenceReference] = field(default_factory=list)
    supplemental_explanation: Optional[str] = None


@dataclass(slots=True)
class ReconstructionRequest:
    input_type: InputType
    content: str
    support_materials: List[str] = field(default_factory=list)


@dataclass(slots=True)
class ReconstructionResponse:
    primary_outputs: List[ReconstructionOutput]
    materials_used: List[str]
