from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.biometrics import OpenCvSFaceAdapter
from app.config import settings
from app.consistency import compare_viz_mrz
from app.document_families import classify_document, get_adapter
from app.evidence_graph import build_evidence_graph
from app.extraction import extract_specimen
from app.intelligence import MockBorderIntelligenceAdapter, ThreatIntelligenceAdapter
from app.linkage import LocalIdentityLinkageStore
from app.mrz import MrzResult, parse_mrz
from app.policy import build_coverage, build_hypotheses, evaluate_hard_gates, plan_next_actions, triage_outcome
from app.quality import assess_capture_quality
from app.validation import validate_document
from app.visual_forensics import LocalDeterministicVisualForensics


def _unavailable(reason: str, source: str) -> dict[str, Any]:
    return {"status": "UNAVAILABLE", "reason": reason, "source": source}


def analyze_integrated(
    specimen_bytes: bytes,
    selfie_bytes: bytes | None = None,
    manual_family: str | None = None,
    case_id: str | None = None,
    intelligence_adapter: ThreatIntelligenceAdapter | None = None,
    database_path: str | None = None,
) -> dict[str, Any]:
    case_id = case_id or str(uuid4())
    capture = assess_capture_quality(specimen_bytes, settings.minimum_image_width, settings.minimum_image_height)
    analysis: dict[str, Any] = {"capture_quality": capture}
    if not capture["acceptable"]:
        analysis.update({
            "document_classification": {"family": manual_family or "UNCLASSIFIED", "method": "QUALITY_GATE_STOP", "confidence": None},
            "extraction": {"visible_fields": {}, "missing_fields": [], "raw_ocr_text": "", "ocr_metadata": {"error": "Capture-quality hard gate stopped OCR."}},
            "mrz": {"mrz_detected": False, "fields": {}, "checks": {}, "raw_lines": [], "error": "Capture-quality hard gate stopped MRZ extraction."},
            "document_rules": [], "cross_source_consistency": [],
            "visual_forensics": _unavailable("Capture-quality gate stopped downstream analysis.", "VEDA_LOCAL_IMAGE_FORENSICS"),
            "biometric_verification": _unavailable("Capture-quality gate stopped downstream analysis.", "LOCAL_PROTOTYPE_BIOMETRICS"),
            "threat_intelligence": _unavailable("No extracted identifier was available after the capture-quality gate.", "LOCAL PROTOTYPE WATCHLIST"),
            "identity_linkage": _unavailable("No usable biometric embedding was produced.", "LOCAL_PROTOTYPE_IDENTITY_LINKAGE"),
        })
        coverage = build_coverage(analysis, family_supports_mrz=manual_family == "TRAVEL_DOCUMENT", selfie_supplied=bool(selfie_bytes), intelligence_mandatory=settings.threat_intelligence_mandatory)
        gates = evaluate_hard_gates(analysis, coverage, biometric_required=bool(selfie_bytes))
        analysis["evidence_coverage"] = coverage
        analysis["hard_gates"] = gates
        analysis["forensic_hypotheses"] = build_hypotheses(analysis, coverage)
        analysis["next_best_actions"] = plan_next_actions(analysis, coverage, gates)
        analysis["evidence_graph"] = build_evidence_graph(analysis)
        analysis["outcome"], analysis["outcome_reasons"] = triage_outcome(analysis, gates)
        return analysis

    extracted = extract_specimen(specimen_bytes)
    analysis["extraction"] = extracted
    classification = classify_document(extracted.get("raw_ocr_text", ""), manual_family)
    analysis["document_classification"] = classification
    adapter = get_adapter(classification["family"])

    if adapter.supports_mrz:
        parsed = parse_mrz(extracted["raw_mrz_text"])
        mrz_payload = {"mrz_detected": parsed.detected, "fields": parsed.fields, "checks": parsed.checks, "raw_lines": parsed.raw_lines, "error": parsed.error, "applicability": "APPLICABLE"}
        comparisons = compare_viz_mrz(extracted["visible_fields"], parsed.fields)
    else:
        parsed = MrzResult(detected=False, fields={}, checks={}, raw_lines=[], error="MRZ is not applicable to this document family.")
        mrz_payload = {"mrz_detected": False, "fields": {}, "checks": {}, "raw_lines": [], "error": None, "applicability": "NOT_APPLICABLE"}
        comparisons = [{"field": field, "source_a": "VIZ", "value_a": extracted["visible_fields"].get(field), "source_b": "MRZ", "value_b": None, "status": "NOT_APPLICABLE", "severity": "INFO", "reason": "MRZ comparison is not applicable to this document family."} for field in ("holder_name", "document_number", "nationality", "date_of_birth", "sex", "expiry_date")]
    analysis["mrz"] = mrz_payload
    analysis["cross_source_consistency"] = comparisons
    analysis["document_rules"] = validate_document(extracted["visible_fields"], parsed, adapter.required_fields, adapter.supports_mrz)

    try:
        analysis["visual_forensics"] = LocalDeterministicVisualForensics().analyze(specimen_bytes) if settings.visual_forensics_enabled else _unavailable("Local visual forensics is disabled.", "VEDA_LOCAL_IMAGE_FORENSICS")
    except Exception as exc:  # lane isolation is deliberate
        analysis["visual_forensics"] = _unavailable(f"Visual-forensics lane failed: {type(exc).__name__}.", "VEDA_LOCAL_IMAGE_FORENSICS")

    biometric_adapter = OpenCvSFaceAdapter(settings.face_detector_model, settings.face_recognizer_model, settings.face_match_threshold, settings.biometrics_enabled)
    try:
        biometric = biometric_adapter.verify(specimen_bytes, selfie_bytes, adapter.portrait_region)
    except Exception as exc:  # lane isolation is deliberate
        biometric = _unavailable(f"Biometric lane failed: {type(exc).__name__}.", "LOCAL_PROTOTYPE_BIOMETRICS")
    analysis["biometric_verification"] = biometric

    intel = intelligence_adapter or MockBorderIntelligenceAdapter(available=settings.mock_border_intelligence_enabled)
    try:
        analysis["threat_intelligence"] = intel.check(extracted["visible_fields"].get("document_number"), extracted["visible_fields"].get("holder_name"))
    except Exception as exc:
        analysis["threat_intelligence"] = _unavailable(f"Threat-intelligence lane failed: {type(exc).__name__}.", "LOCAL PROTOTYPE WATCHLIST")

    try:
        linkage = LocalIdentityLinkageStore(database_path or settings.case_database_path, settings.identity_linkage_threshold)
        analysis["identity_linkage"] = linkage.search_and_enrol(case_id, extracted["visible_fields"].get("holder_name"), extracted["visible_fields"].get("document_number"), biometric.get("_embedding"))
    except Exception as exc:
        analysis["identity_linkage"] = _unavailable(f"Identity-linkage lane failed: {type(exc).__name__}.", "LOCAL_PROTOTYPE_IDENTITY_LINKAGE")

    coverage = build_coverage(analysis, adapter.supports_mrz, bool(selfie_bytes), settings.threat_intelligence_mandatory)
    gates = evaluate_hard_gates(analysis, coverage, biometric_required=bool(selfie_bytes))
    analysis["evidence_coverage"] = coverage
    analysis["hard_gates"] = gates
    analysis["forensic_hypotheses"] = build_hypotheses(analysis, coverage)
    analysis["next_best_actions"] = plan_next_actions(analysis, coverage, gates)
    analysis["evidence_graph"] = build_evidence_graph(analysis)
    analysis["outcome"], analysis["outcome_reasons"] = triage_outcome(analysis, gates)
    analysis["analyzed_at"] = datetime.now(timezone.utc).isoformat()
    return analysis
