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
    LOW_RISK = "LOW_RISK"
    REFER = "REFER"
    HIGH_RISK = "HIGH_RISK"
    INDETERMINATE = "INDETERMINATE"


class DocumentFamily(str, Enum):
    TRAVEL_DOCUMENT = "TRAVEL_DOCUMENT"
    VISA_OR_PERMIT = "VISA_OR_PERMIT"
    NATIONAL_ID = "NATIONAL_ID"
    DRIVING_LICENCE = "DRIVING_LICENCE"


class CoverageExecutionState(str, Enum):
    COMPLETED = "COMPLETED"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    FAILED_TO_EXECUTE = "FAILED_TO_EXECUTE"


class EvidenceItem(BaseModel):
    evidence_id: str
    title: str
    summary: str
    state: EvidenceState
    severity: str = "INFO"
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
    lanes: list[dict[str, Any]] = Field(default_factory=list)


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
    outcome_reasons: list[str] = Field(default_factory=list)
    visible_document_data: dict[str, Any] = Field(default_factory=dict)
    visible_document: dict[str, Any] = Field(default_factory=dict)
    mrz_analysis: dict[str, Any] = Field(default_factory=dict)
    document_rules: list[dict[str, Any]] = Field(default_factory=list)
    cross_source_consistency: list[dict[str, Any]] = Field(default_factory=list)
    threat_intelligence: dict[str, Any] = Field(default_factory=dict)
    case_id: str | None = None
    created_at: str | None = None
    document_family: str | None = None
    capture_quality: dict[str, Any] = Field(default_factory=dict)
    visual_forensics: dict[str, Any] = Field(default_factory=dict)
    biometric_verification: dict[str, Any] = Field(default_factory=dict)
    identity_linkage: dict[str, Any] = Field(default_factory=dict)
    evidence_graph: dict[str, Any] = Field(default_factory=dict)
    forensic_hypotheses: list[dict[str, Any]] = Field(default_factory=list)
    next_best_actions: list[dict[str, Any]] = Field(default_factory=list)
    hard_gates: list[dict[str, Any]] = Field(default_factory=list)
    triage_risk_index: float | None = None
    triage_risk_label: str | None = None
    audit_trail: list[dict[str, Any]] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    disclaimer: str = "Research-prototype decision support. Human review is required; triage outcomes are policy-driven and are not fraud probabilities."


def unavailable_lane(lane_id: str, name: str, required: bool = True) -> EvidenceLane:
    item = EvidenceItem(
        evidence_id=f"{lane_id}.unavailable",
        title=f"{name} unavailable",
        summary="No implementation is present for this evidence lane in the current task.",
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


def _lane(lane_id: str, name: str, status: str, summary: str, evidence: list[EvidenceItem], required: bool = True, provider: str | None = None) -> EvidenceLane:
    return EvidenceLane(lane_id=lane_id, name=name, status=EvidenceState(status), summary=summary, required=required, evidence_items=evidence, provider=provider)


def build_task04_autopsy(scan_id: str, filename: str, sha256: str, analysis: dict[str, Any], intelligence_mandatory: bool = True) -> IdentityForensicAutopsy:
    extraction = analysis["extraction"]
    mrz = analysis["mrz"]
    rules = analysis["document_rules"]
    comparisons = analysis["cross_source_consistency"]
    intelligence = analysis["threat_intelligence"]
    extraction_status = "PASS" if not extraction["missing_fields"] and not extraction["ocr_metadata"].get("error") else "UNAVAILABLE"
    mrz_status = "UNAVAILABLE" if not mrz["mrz_detected"] else ("FAIL" if any(status == "FAIL" for status in mrz["checks"].values()) else "PASS")
    rules_status = "FAIL" if any(rule["status"] == "FAIL" for rule in rules) else ("UNAVAILABLE" if any(rule["status"] == "UNAVAILABLE" for rule in rules) else "PASS")
    consistency_status = "FAIL" if any(item["status"] == "FAIL" for item in comparisons) else ("UNAVAILABLE" if any(item["status"] == "UNAVAILABLE" for item in comparisons) else "PASS")
    lanes = [
        _lane("document.extraction", "Visible document extraction", extraction_status, "Visible fields were extracted from local image pixels." if extraction_status == "PASS" else "Required visible fields could not all be extracted from image pixels.", [EvidenceItem(evidence_id="document.extraction.pixels", title="Pixel-only local OCR", summary=f"Tesseract extraction status: {extraction_status}.", state=EvidenceState(extraction_status), source={"kind": "image_pixels", "provider": "tesseract-local"})]),
        _lane("document.mrz", "MRZ extraction and checks", mrz_status, "MRZ was parsed from image pixels." if mrz_status == "PASS" else "MRZ could not be parsed from image pixels.", [EvidenceItem(evidence_id="document.mrz.parsed", title="MRZ parsed from pixels", summary=mrz.get("error") or "Two fictional MRZ lines parsed.", state=EvidenceState(mrz_status), source={"kind": "image_pixels", "provider": "tesseract-local"})]),
        _lane("document.validation", "Deterministic document rules", rules_status, "Deterministic rules completed.", [EvidenceItem(evidence_id=f"document.validation.{rule['rule_id']}", title=rule["rule_id"], summary=rule["reason"], state=EvidenceState(rule["status"]), severity="HIGH" if rule["status"] == "FAIL" else "INFO", source={"kind": "deterministic_rule"}) for rule in rules]),
        _lane("cross_source.consistency", "VIZ to MRZ consistency", consistency_status, "Field-by-field VIZ and MRZ comparison completed." if consistency_status != "UNAVAILABLE" else "One or more required comparisons are unavailable.", [EvidenceItem(evidence_id=f"cross_source.{item['field']}", title=f"VIZ/MRZ {item['field']} comparison", summary=item["reason"], state=EvidenceState(item["status"]), severity=item["severity"], source={"kind": "cross_source", "sources": ["VIZ", "MRZ"]}) for item in comparisons]),
        _lane("threat_intelligence", "DEMO mock border intelligence", intelligence["status"], intelligence["reason"], [EvidenceItem(evidence_id="threat_intelligence.mock_lookup", title="DEMO mock intelligence lookup", summary=intelligence["reason"], state=EvidenceState(intelligence["status"]), severity="CRITICAL" if intelligence["status"] == "FAIL" else "INFO", source={"kind": "mock_local", "provider": "MOCK_BORDER_INTELLIGENCE"})], required=intelligence_mandatory, provider="MOCK_BORDER_INTELLIGENCE"),
        unavailable_lane("forensics.visual_tamper", "Visual tamper forensics"),
        unavailable_lane("biometrics.face_verify", "Biometric verification"),
        unavailable_lane("electronic_credential.nfc", "NFC / ePassport evidence", required=False),
    ]
    missing = [lane.lane_id for lane in lanes if lane.required and lane.status == EvidenceState.UNAVAILABLE]
    total = sum(lane.required for lane in lanes)
    completed = total - len(missing)
    coverage = EvidenceCoverage(mandatory_total=total, mandatory_completed=completed, coverage_ratio=completed / total if total else 1.0, missing_mandatory=missing, state="INCOMPLETE" if missing else "COMPLETE")
    findings = [item["reason"] + f" VIZ={item['value_a']!r}; MRZ={item['value_b']!r}." for item in comparisons if item["status"] == "FAIL"]
    if intelligence["status"] == "FAIL":
        findings.append("DEMO MOCK INTELLIGENCE: " + intelligence["reason"])
    if missing:
        findings.append("Required evidence lanes are unavailable: " + ", ".join(missing))
    reason_ids = [f"cross_source.{item['field']}" for item in comparisons if item["status"] == "FAIL"]
    if intelligence["status"] == "FAIL":
        reason_ids.append("threat_intelligence.mock_lookup")
    reason_ids.extend(lane.evidence_items[0].evidence_id for lane in lanes if lane.lane_id in missing)
    return IdentityForensicAutopsy(
        scan_id=scan_id, specimen_filename=filename, specimen_sha256=sha256,
        document_type="VEDA_FICTIONAL_CREDENTIAL" if extraction_status == "PASS" else "UNCLASSIFIED_SPECIMEN",
        extracted_identity=extraction["visible_fields"], evidence_lanes=lanes, evidence_coverage=coverage,
        outcome=ScreeningOutcome.INDETERMINATE if missing else (ScreeningOutcome.REFER if any(lane.status == EvidenceState.FAIL for lane in lanes) else ScreeningOutcome.CLEAR),
        critical_findings=findings, outcome_reasons=reason_ids,
        visible_document_data=extraction, visible_document=extraction, mrz_analysis=mrz,
        document_rules=rules, cross_source_consistency=comparisons, threat_intelligence=intelligence,
    )
