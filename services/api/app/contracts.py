from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class EvidenceState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SUSPICIOUS = "SUSPICIOUS"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ScreeningOutcome(str, Enum):
    CLEAR = "CLEAR"
    REFER = "REFER"
    INDETERMINATE = "INDETERMINATE"


class EvidenceItem(BaseModel):
    evidence_id: str
    title: str
    summary: str
    state: EvidenceState
    source: dict[str, Any] = Field(default_factory=dict)


class EvidenceLane(BaseModel):
    lane_id: str
    name: str
    status: EvidenceState
    summary: str
    required: bool = True
    evidence_items: list[EvidenceItem] = Field(default_factory=list)
    provider: str | None = None


class EvidenceCoverage(BaseModel):
    mandatory_total: int
    mandatory_completed: int
    coverage_ratio: float
    missing_mandatory: list[str] = Field(default_factory=list)
    state: str


class IdentityForensicAutopsy(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    scan_id: str
    specimen_filename: str
    specimen_sha256: str
    document_type: str = "UNCLASSIFIED_SPECIMEN"
    extracted_identity: dict[str, Any] = Field(default_factory=dict)
    evidence_lanes: list[EvidenceLane]
    evidence_coverage: EvidenceCoverage
    outcome: ScreeningOutcome
    critical_findings: list[str] = Field(default_factory=list)
    visible_document: dict[str, Any] = Field(default_factory=dict)
    mrz_analysis: dict[str, Any] = Field(default_factory=dict)
    document_rules: list[dict[str, Any]] = Field(default_factory=list)
    disclaimer: str = "Decision support only. Human review is required; no fraud probability is asserted."


def unavailable_lane(lane_id: str, name: str, required: bool = True) -> EvidenceLane:
    item = EvidenceItem(
        evidence_id=f"{lane_id}.unavailable",
        title=f"{name} unavailable",
        summary="Task 01 provides no detector for this evidence lane yet.",
        state=EvidenceState.UNAVAILABLE,
        source={"kind": "placeholder", "provider": None},
    )
    return EvidenceLane(
        lane_id=lane_id,
        name=name,
        status=EvidenceState.UNAVAILABLE,
        summary="Required evidence is currently unavailable.",
        required=required,
        evidence_items=[item],
    )


def build_placeholder_autopsy(scan_id: str, filename: str, sha256: str) -> IdentityForensicAutopsy:
    lanes = [
        unavailable_lane("document.extraction", "Document extraction"),
        unavailable_lane("document.validation", "Document validation"),
        unavailable_lane("forensics.visual_tamper", "Visual forensics"),
        unavailable_lane("biometrics.face_verify", "Biometric verification"),
    ]
    missing = [lane.lane_id for lane in lanes if lane.required and lane.status == EvidenceState.UNAVAILABLE]
    total = sum(lane.required for lane in lanes)
    completed = total - len(missing)
    coverage = EvidenceCoverage(
        mandatory_total=total,
        mandatory_completed=completed,
        coverage_ratio=completed / total if total else 1.0,
        missing_mandatory=missing,
        state="INCOMPLETE" if missing else "COMPLETE",
    )
    return IdentityForensicAutopsy(
        scan_id=scan_id,
        specimen_filename=filename,
        specimen_sha256=sha256,
        evidence_lanes=lanes,
        evidence_coverage=coverage,
        outcome=ScreeningOutcome.INDETERMINATE,
        critical_findings=["Required evidence lanes are unavailable: " + ", ".join(missing)],
    )
