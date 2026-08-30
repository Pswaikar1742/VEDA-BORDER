from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.contracts import EvidenceItem, EvidenceLane, EvidenceState, IdentityForensicAutopsy, ScreeningOutcome, unavailable_lane


def _state(value: str) -> EvidenceState:
    return EvidenceState(value if value in EvidenceState._value2member_map_ else "UNAVAILABLE")


def _lane(lane_id: str, name: str, status: str, summary: str, required: bool, source: str, severity: str = "INFO") -> EvidenceLane:
    state = _state(status)
    return EvidenceLane(
        lane_id=lane_id,
        name=name,
        status=state,
        summary=summary,
        required=required,
        provider=source,
        evidence_items=[EvidenceItem(evidence_id=f"{lane_id}.result", title=name, summary=summary, state=state, severity=severity, source={"provider": source, "provenance": "local_runtime"})],
    )


def build_integrated_autopsy(case_id: str, filename: str, digest: str, analysis: dict[str, Any], selfie_supplied: bool) -> IdentityForensicAutopsy:
    extraction = analysis.get("extraction", {})
    mrz = analysis.get("mrz", {})
    rules = analysis.get("document_rules", [])
    consistency = analysis.get("cross_source_consistency", [])
    visual = analysis.get("visual_forensics", {})
    biometric_internal = analysis.get("biometric_verification", {})
    biometric = {key: value for key, value in biometric_internal.items() if key != "_embedding"}
    intelligence = analysis.get("threat_intelligence", {})
    linkage = analysis.get("identity_linkage", {})
    family = analysis.get("document_classification", {}).get("family", "UNCLASSIFIED")
    mrz_applicable = mrz.get("applicability") != "NOT_APPLICABLE"

    extraction_status = "PASS" if extraction.get("visible_fields") and not extraction.get("ocr_metadata", {}).get("error") else "UNAVAILABLE"
    mrz_status = "NOT_APPLICABLE" if not mrz_applicable else ("UNAVAILABLE" if not mrz.get("mrz_detected") else ("FAIL" if "FAIL" in mrz.get("checks", {}).values() else "PASS"))
    rules_status = "UNAVAILABLE" if not rules else ("FAIL" if any(rule["status"] == "FAIL" for rule in rules) else "PASS")
    consistency_status = "NOT_APPLICABLE" if not mrz_applicable else ("UNAVAILABLE" if not consistency else ("FAIL" if any(item["status"] == "FAIL" for item in consistency) else ("UNAVAILABLE" if any(item["status"] == "UNAVAILABLE" for item in consistency) else "PASS")))
    capture = analysis.get("capture_quality", {})
    lanes = [
        _lane("capture.quality", "Capture quality", capture.get("status", "UNAVAILABLE"), "Image quality passed configured capture checks." if capture.get("acceptable") else "Image quality requires recapture before dependable extraction.", True, "VEDA_LOCAL_CAPTURE_QUALITY", "HIGH" if not capture.get("acceptable") else "INFO"),
        _lane("document.extraction", "Visible document extraction", extraction_status, "Visible fields were extracted from submitted pixels." if extraction_status == "PASS" else "Visible extraction did not complete.", True, "TESSERACT_LOCAL"),
        _lane("document.mrz", "MRZ verification", mrz_status, "Machine-readable evidence was parsed and its check digits evaluated." if mrz_status == "PASS" else ("MRZ does not apply to this family." if mrz_status == "NOT_APPLICABLE" else "MRZ evidence did not complete or failed validation."), mrz_applicable, "TESSERACT_LOCAL_MRZ"),
        _lane("document.validation", "Deterministic document rules", rules_status, "Family-aware deterministic validity rules executed." if rules else "Document rules did not execute.", True, "DETERMINISTIC_RULE_ENGINE", "HIGH" if rules_status == "FAIL" else "INFO"),
        _lane("cross_source.consistency", "Cross-source consistency", consistency_status, "VIZ and MRZ values were compared semantically." if mrz_applicable else "Cross-source MRZ comparison does not apply to this family.", mrz_applicable, "DETERMINISTIC_CONSISTENCY_ENGINE", "CRITICAL" if consistency_status == "FAIL" else "INFO"),
        _lane("forensics.visual_tamper", "Visual forensics", visual.get("status", "UNAVAILABLE"), visual.get("limitations", [visual.get("reason", "Visual analysis unavailable.")])[0], True, visual.get("detector", {}).get("name", "VEDA_LOCAL_IMAGE_FORENSICS"), "HIGH" if visual.get("status") == "SUSPICIOUS" else "INFO"),
        _lane("biometrics.face_verify", "Face verification", biometric.get("status", "UNAVAILABLE"), biometric.get("reason", "Face verification unavailable."), selfie_supplied, biometric.get("model", "LOCAL_PROTOTYPE_BIOMETRICS"), "CRITICAL" if biometric.get("status") == "FAIL" else "INFO"),
        _lane("threat_intelligence", "Threat intelligence", intelligence.get("status", "UNAVAILABLE"), intelligence.get("reason", "Local prototype watchlist unavailable."), True, intelligence.get("display_source", "LOCAL PROTOTYPE WATCHLIST"), "CRITICAL" if intelligence.get("status") == "FAIL" else "INFO"),
        _lane("identity.linkage", "Identity linkage", linkage.get("status", "UNAVAILABLE"), linkage.get("reason", "Identity linkage unavailable."), False, "LOCAL_PROTOTYPE_IDENTITY_LINKAGE", "HIGH" if linkage.get("status") == "SUSPICIOUS" else "INFO"),
        unavailable_lane("electronic_credential", "Electronic credential", required=False),
    ]
    hard_gates = analysis.get("hard_gates", [])
    critical = [gate["reason"] for gate in hard_gates]
    created_at = analysis.get("analyzed_at") or datetime.now(timezone.utc).isoformat()
    outcome_val = analysis["outcome"]
    if outcome_val == "HIGH_RISK":
        risk_index = 90.0
        risk_label = "HIGH RISK (HARD GATE / CRITICAL CONTRADICTION)"
    elif outcome_val == "REFER":
        risk_index = 55.0
        risk_label = "MODERATE RISK (FORENSIC / STATUS REVIEW REQUIRED)"
    elif outcome_val == "LOW_RISK":
        risk_index = 8.0
        risk_label = "LOW RISK (CONSISTENT EVIDENCE ACROSS COMPLETED LANES)"
    else:  # INDETERMINATE
        risk_index = None
        risk_label = "INDETERMINATE (MANDATORY EVIDENCE INCOMPLETE)"

    return IdentityForensicAutopsy(
        scan_id=case_id,
        case_id=case_id,
        created_at=created_at,
        specimen_filename=filename,
        specimen_sha256=digest,
        document_type=family,
        document_family=family,
        extracted_identity=extraction.get("visible_fields", {}),
        evidence_lanes=lanes,
        evidence_coverage=analysis["evidence_coverage"],
        outcome=ScreeningOutcome(analysis["outcome"]),
        critical_findings=critical,
        outcome_reasons=analysis.get("outcome_reasons", []),
        visible_document_data=extraction,
        visible_document=extraction,
        mrz_analysis=mrz,
        document_rules=rules,
        cross_source_consistency=consistency,
        threat_intelligence=intelligence,
        capture_quality=capture,
        visual_forensics=visual,
        biometric_verification=biometric,
        identity_linkage=linkage,
        evidence_graph=analysis.get("evidence_graph", {}),
        forensic_hypotheses=analysis.get("forensic_hypotheses", []),
        next_best_actions=analysis.get("next_best_actions", []),
        hard_gates=hard_gates,
        triage_risk_index=risk_index,
        triage_risk_label=risk_label,
        audit_trail=[
            {"timestamp": created_at, "event": "CASE_CREATED", "actor": "LOCAL_OFFICER_WORKSTATION"},
            {"timestamp": created_at, "event": "ANALYSIS_COMPLETED", "actor": "IDENTITY_FORENSIC_AUTOPSY_ENGINE", "outcome": analysis["outcome"]},
        ],
        limitations=[
            "Research-prototype screening outcome; not a calibrated fraud probability or authenticity determination.",
            "Local watchlist records and generated fixtures are synthetic prototype data.",
            "No operational government, INTERPOL, ICAO PKD, Passport Seva, MHA, or SSB integration is active.",
        ],
    )
