from __future__ import annotations

from typing import Any


CRITICAL_CONSISTENCY_FIELDS = {"holder_name", "document_number", "date_of_birth"}


def _lane(lane: str, execution: str, evidence: str, mandatory: bool) -> dict[str, Any]:
    return {"lane": lane, "execution_status": execution, "evidence_status": evidence,
            "state": execution, "mandatory": mandatory}


def build_coverage(analysis: dict[str, Any], family_supports_mrz: bool, selfie_supplied: bool,
                   intelligence_mandatory: bool) -> dict[str, Any]:
    """Report execution and evidence sufficiency separately.

    A completed lane is not automatically sufficient evidence.  In particular,
    failed checks remain visible to policy and unavailable mandatory evidence
    makes the result indeterminate.
    """
    extraction = analysis.get("extraction", {}) or {}
    extraction_ok = bool(extraction) and not extraction.get("ocr_metadata", {}).get("error") and not extraction.get("missing_fields")
    mrz = analysis.get("mrz", {}) or {}
    if not family_supports_mrz:
        mrz_lane = _lane("mrz", "NOT_APPLICABLE", "NOT_APPLICABLE", False)
        consistency_lane = _lane("cross_source_consistency", "NOT_APPLICABLE", "NOT_APPLICABLE", False)
    elif mrz.get("mrz_detected"):
        mrz_failed = any(value == "FAIL" for value in (mrz.get("checks") or {}).values())
        mrz_lane = _lane("mrz", "COMPLETED", "FAIL" if mrz_failed else "PASS", True)
        comparisons = analysis.get("cross_source_consistency") or []
        consistency_status = "FAIL" if any(i.get("status") == "FAIL" for i in comparisons) else ("PASS" if comparisons and all(i.get("status") == "PASS" for i in comparisons) else "UNAVAILABLE")
        consistency_lane = _lane("cross_source_consistency", "COMPLETED", consistency_status, True)
    else:
        mrz_lane = _lane("mrz", "COMPLETED", "UNAVAILABLE", True)
        consistency_lane = _lane("cross_source_consistency", "COMPLETED", "UNAVAILABLE", True)
    rules = analysis.get("document_rules") or []
    rules_status = "FAIL" if any(r.get("status") == "FAIL" for r in rules) else ("PASS" if rules and all(r.get("status") == "PASS" for r in rules) else "UNAVAILABLE")
    visual_status = (analysis.get("visual_forensics") or {}).get("status")
    visual_status = visual_status if visual_status in {"PASS", "FAIL", "SUSPICIOUS"} else "UNAVAILABLE"
    bio = analysis.get("biometric_verification") or {}
    bio_status = bio.get("status") if bio.get("status") in {"PASS", "FAIL", "SUSPICIOUS"} else "UNAVAILABLE"
    intel = analysis.get("threat_intelligence") or {}
    intel_status = intel.get("status") if intel.get("status") in {"PASS", "FAIL", "SUSPICIOUS"} else "UNAVAILABLE"
    link = analysis.get("identity_linkage") or {}
    link_status = link.get("status") if link.get("status") in {"PASS", "FAIL", "SUSPICIOUS"} else "UNAVAILABLE"
    lanes = [
        _lane("document_data", "COMPLETED" if extraction else "FAILED_TO_EXECUTE", "PASS" if extraction_ok else "UNAVAILABLE", True),
        mrz_lane,
        _lane("document_rules", "COMPLETED" if rules else "FAILED_TO_EXECUTE", rules_status, True),
        consistency_lane,
        _lane("visual_forensics", "COMPLETED" if visual_status != "UNAVAILABLE" else "FAILED_TO_EXECUTE", visual_status, True),
        _lane("biometrics", "NOT_APPLICABLE" if not selfie_supplied else "COMPLETED", "NOT_APPLICABLE" if not selfie_supplied else bio_status, selfie_supplied),
        _lane("threat_intelligence", "COMPLETED" if intel_status != "UNAVAILABLE" else "UNAVAILABLE", intel_status, intelligence_mandatory),
        _lane("identity_linkage", "COMPLETED" if link_status != "UNAVAILABLE" else "UNAVAILABLE", link_status, False),
        _lane("electronic_credential", "UNAVAILABLE" if family_supports_mrz else "NOT_APPLICABLE", "UNAVAILABLE" if family_supports_mrz else "NOT_APPLICABLE", False),
    ]
    mandatory = [lane for lane in lanes if lane["mandatory"]]
    adequate = [lane for lane in mandatory if lane["evidence_status"] == "PASS"]
    missing = [lane["lane"] for lane in mandatory if lane["evidence_status"] == "UNAVAILABLE"]
    failed = [lane["lane"] for lane in mandatory if lane["evidence_status"] in {"FAIL", "SUSPICIOUS"}]
    return {"mandatory_total": len(mandatory), "mandatory_completed": len(adequate),
            "adequate_mandatory": len(adequate), "coverage_ratio": round(len(adequate) / len(mandatory), 4) if mandatory else 1.0,
            "missing_mandatory": missing, "failed_mandatory": failed,
            "evidence_sufficient": not missing and not failed,
            "state": "COMPLETE" if not missing else "INCOMPLETE", "lanes": lanes}


def evaluate_hard_gates(analysis: dict[str, Any], coverage: dict[str, Any], biometric_required: bool) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []
    for item in analysis.get("cross_source_consistency", []):
        if item.get("status") == "FAIL" and item.get("field") in CRITICAL_CONSISTENCY_FIELDS:
            gates.append({"gate": "CRITICAL_CROSS_SOURCE_CONTRADICTION", "triggered": True, "severity": "CRITICAL", "evidence": f"cross_source.{item['field']}", "reason": item["reason"]})
        elif item.get("status") == "FAIL":
            gates.append({"gate": "CROSS_SOURCE_CONTRADICTION", "triggered": True, "severity": "HIGH", "evidence": f"cross_source.{item.get('field')}", "reason": item.get("reason", "Visible and machine-readable fields disagree.")})
    mrz_checks = (analysis.get("mrz") or {}).get("checks") or {}
    if any(value == "FAIL" for value in mrz_checks.values()):
        gates.append({"gate": "MRZ_CHECKSUM_FAILURE", "triggered": True, "severity": "CRITICAL", "evidence": "document.mrz.checks", "reason": "One or more required MRZ check digits failed."})
    intelligence = analysis.get("threat_intelligence", {})
    if intelligence.get("result") in {"DOCUMENT_BLACKLISTED", "IDENTITY_WATCHLIST_MATCH"}:
        gates.append({"gate": "LOCAL_PROTOTYPE_WATCHLIST_HIT", "triggered": True, "severity": "CRITICAL", "evidence": "threat_intelligence.local_lookup", "reason": intelligence.get("reason")})
    biometric = analysis.get("biometric_verification", {})
    if biometric_required and biometric.get("decision") == "MISMATCH":
        gates.append({"gate": "REQUIRED_BIOMETRIC_MISMATCH", "triggered": True, "severity": "CRITICAL", "evidence": "biometrics.face_verify", "reason": biometric.get("reason")})
    expired = next((rule for rule in analysis.get("document_rules", []) if rule.get("rule_id") == "date.expiry.current" and rule.get("status") == "FAIL"), None)
    if expired:
        gates.append({"gate": "EXPIRED_DOCUMENT", "triggered": True, "severity": "HIGH", "evidence": "document.validation.date.expiry.current", "reason": expired["reason"]})
    if any(rule.get("status") == "FAIL" for rule in analysis.get("document_rules", [])) and not expired:
        gates.append({"gate": "DOCUMENT_VALIDATION_FAILURE", "triggered": True, "severity": "HIGH", "evidence": "document.validation", "reason": "A required deterministic document rule failed."})
    if coverage.get("missing_mandatory"):
        gates.append({"gate": "MANDATORY_EVIDENCE_INCOMPLETE", "triggered": True, "severity": "HIGH", "evidence": "evidence_coverage", "reason": "Mandatory evidence is incomplete: " + ", ".join(coverage["missing_mandatory"])})
    return gates


def triage_outcome(analysis: dict[str, Any], hard_gates: list[dict[str, Any]]) -> tuple[str, list[str]]:
    if any(gate["gate"] == "MANDATORY_EVIDENCE_INCOMPLETE" for gate in hard_gates):
        return "INDETERMINATE", [gate["reason"] for gate in hard_gates]
    if any(gate["severity"] == "CRITICAL" for gate in hard_gates):
        return "HIGH_RISK", [gate["reason"] for gate in hard_gates]
    if hard_gates or analysis.get("visual_forensics", {}).get("status") == "SUSPICIOUS" or analysis.get("identity_linkage", {}).get("status") == "SUSPICIOUS":
        return "REFER", [gate["reason"] for gate in hard_gates] or ["One or more local forensic lanes require officer review."]
    return "LOW_RISK", ["No configured hard gate or current cross-source contradiction was triggered within completed prototype evidence."]


def build_hypotheses(analysis: dict[str, Any], coverage: dict[str, Any]) -> list[dict[str, Any]]:
    hypotheses: list[dict[str, Any]] = []
    mismatches = [item for item in analysis.get("cross_source_consistency", []) if item.get("status") == "FAIL"]
    if any(item["field"] in {"holder_name", "document_number", "date_of_birth", "nationality", "sex", "expiry_date"} for item in mismatches):
        hypotheses.append(_hypothesis("POSSIBLE_VISIBLE_BIOGRAPHIC_FIELD_ALTERATION", "CRITICAL", [f"cross_source.{item['field']}" for item in mismatches], [], [], "Visible biographic data conflicts with independently read MRZ evidence.", "The contradiction identifies disagreement, not the physical alteration method."))
    biometric = analysis.get("biometric_verification", {})
    if biometric.get("decision") == "MISMATCH":
        hypotheses.append(_hypothesis("POSSIBLE_PORTRAIT_SUBSTITUTION", "CRITICAL", ["biometrics.face_verify"], [], [], "The document portrait and supplied live/uploaded face do not meet the local prototype match threshold.", "A mismatch may also arise from capture conditions, aging, occlusion, or model limitations."))
    if analysis.get("identity_linkage", {}).get("status") == "SUSPICIOUS":
        hypotheses.append(_hypothesis("POSSIBLE_MULTI_IDENTITY_USAGE", "HIGH", ["identity_linkage.local_embedding"], [], [], "A similar biometric embedding is associated with substantially different claimed identity data.", "Similarity is not a legal identity conclusion."))
    if analysis.get("threat_intelligence", {}).get("status") == "FAIL" or any(rule.get("rule_id") == "date.expiry.current" and rule.get("status") == "FAIL" for rule in analysis.get("document_rules", [])):
        hypotheses.append(_hypothesis("DOCUMENT_STATUS_ALERT", "CRITICAL", ["threat_intelligence.local_lookup", "document.validation.date.expiry.current"], [], [], "A deterministic document-status or local prototype watchlist alert is present.", "The watchlist is local synthetic prototype data only."))
    if analysis.get("visual_forensics", {}).get("status") == "SUSPICIOUS":
        hypotheses.append(_hypothesis("POSSIBLE_DOCUMENT_REGION_MANIPULATION", "HIGH", ["forensics.visual"], [], [], "Local image-forensic measures identify one or more anomalous regions.", "Deterministic visual heuristics can produce false positives and do not establish authenticity."))
    if coverage.get("state") != "COMPLETE":
        hypotheses.append(_hypothesis("INSUFFICIENT_FORENSIC_COVERAGE", "HIGH", ["evidence_coverage"], [], coverage.get("missing_mandatory", []), "One or more policy-mandatory evidence lanes did not complete.", "No definitive low-risk clearance is permitted with missing mandatory evidence."))
    if not mismatches:
        hypotheses.append(_hypothesis("NO_CURRENT_CROSS_SOURCE_CONTRADICTION", "INFO", ["cross_source.consistency"], [], [], "Completed VIZ and MRZ comparisons do not currently contradict each other.", "Consistency does not establish real-world authenticity."))
    return hypotheses


def _hypothesis(identifier: str, severity: str, supporting: list[str], contradicting: list[str], missing: list[str], explanation: str, limitations: str) -> dict[str, Any]:
    return {"hypothesis": identifier, "severity": severity, "supporting_evidence": supporting, "contradicting_evidence": contradicting, "missing_evidence": missing, "explanation": explanation, "limitations": limitations}


def plan_next_actions(analysis: dict[str, Any], coverage: dict[str, Any], hard_gates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if analysis.get("capture_quality", {}).get("acceptable") is False:
        actions.append(_action("RECAPTURE_DOCUMENT", 1, "Capture-quality checks did not meet extraction thresholds."))
    mismatch_fields = [item["field"] for item in analysis.get("cross_source_consistency", []) if item.get("status") == "FAIL"]
    if mismatch_fields:
        actions += [_action("RECAPTURE_FIELD_REGION", 1, "Re-read the conflicting region: " + ", ".join(mismatch_fields)), _action("CAPTURE_HIGHER_RESOLUTION_REGION", 2, "Higher-resolution pixels can distinguish OCR error from a stable contradiction."), _action("RUN_VISUAL_FORENSICS", 3, "Inspect the conflicting visible region for local manipulation cues.")]
    biometric = analysis.get("biometric_verification", {})
    if biometric.get("status") == "UNAVAILABLE":
        actions.append(_action("CAPTURE_LIVE_FACE", 2, biometric.get("reason", "Face evidence is unavailable.")))
    elif biometric.get("decision") == "MISMATCH":
        actions.append(_action("RUN_FACE_VERIFICATION", 2, "Repeat with controlled lighting and pose before relying on the mismatch."))
    if analysis.get("threat_intelligence", {}).get("status") == "UNAVAILABLE":
        actions.append(_action("RETRY_THREAT_INTELLIGENCE", 2, "The local prototype watchlist lane did not complete."))
    if hard_gates:
        actions.append(_action("REFER_TO_SECONDARY_INSPECTION", 1, "One or more policy hard gates are active."))
    if any(gate["gate"] in {"CRITICAL_CROSS_SOURCE_CONTRADICTION", "EXPIRED_DOCUMENT"} for gate in hard_gates):
        actions.append(_action("READ_ELECTRONIC_CREDENTIAL", 4, "Use authenticated electronic evidence if an authorized reader becomes available; this adapter is not implemented."))
    unique: dict[str, dict[str, Any]] = {}
    for action in actions:
        if action["action"] not in unique or action["priority"] < unique[action["action"]]["priority"]:
            unique[action["action"]] = action
    return sorted(unique.values(), key=lambda item: (item["priority"], item["action"]))


def _action(action: str, priority: int, reason: str) -> dict[str, Any]:
    return {"action": action, "priority": priority, "reason": reason, "policy_driven": True}
