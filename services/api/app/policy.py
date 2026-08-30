from __future__ import annotations

from typing import Any


CRITICAL_CONSISTENCY_FIELDS = {"holder_name", "document_number", "date_of_birth"}


def build_coverage(analysis: dict[str, Any], family_supports_mrz: bool, selfie_supplied: bool, intelligence_mandatory: bool) -> dict[str, Any]:
    extraction = analysis.get("extraction", {})
    lanes = [
        {"lane": "document_data", "state": "COMPLETED" if extraction and not extraction.get("ocr_metadata", {}).get("error") else "FAILED_TO_EXECUTE", "mandatory": True},
        {"lane": "mrz", "state": ("COMPLETED" if analysis.get("mrz", {}).get("mrz_detected") else "FAILED_TO_EXECUTE") if family_supports_mrz else "NOT_APPLICABLE", "mandatory": family_supports_mrz},
        {"lane": "document_rules", "state": "COMPLETED" if analysis.get("document_rules") else "FAILED_TO_EXECUTE", "mandatory": True},
        {"lane": "cross_source_consistency", "state": ("COMPLETED" if analysis.get("cross_source_consistency") else "FAILED_TO_EXECUTE") if family_supports_mrz else "NOT_APPLICABLE", "mandatory": family_supports_mrz},
        {"lane": "visual_forensics", "state": "COMPLETED" if analysis.get("visual_forensics", {}).get("status") in {"PASS", "SUSPICIOUS", "FAIL"} else "FAILED_TO_EXECUTE", "mandatory": True},
        {"lane": "biometrics", "state": "COMPLETED" if analysis.get("biometric_verification", {}).get("status") in {"PASS", "FAIL"} else "UNAVAILABLE", "mandatory": selfie_supplied},
        {"lane": "threat_intelligence", "state": "COMPLETED" if analysis.get("threat_intelligence", {}).get("status") in {"PASS", "FAIL"} else "UNAVAILABLE", "mandatory": intelligence_mandatory},
        {"lane": "identity_linkage", "state": "COMPLETED" if analysis.get("identity_linkage", {}).get("status") in {"PASS", "SUSPICIOUS"} else "UNAVAILABLE", "mandatory": False},
        {"lane": "electronic_credential", "state": "UNAVAILABLE" if family_supports_mrz else "NOT_APPLICABLE", "mandatory": False},
    ]
    mandatory = [lane for lane in lanes if lane["mandatory"]]
    completed = [lane for lane in mandatory if lane["state"] == "COMPLETED"]
    missing = [lane["lane"] for lane in mandatory if lane["state"] != "COMPLETED"]
    return {
        "mandatory_total": len(mandatory),
        "mandatory_completed": len(completed),
        "coverage_ratio": round(len(completed) / len(mandatory), 4) if mandatory else 1.0,
        "missing_mandatory": missing,
        "state": "COMPLETE" if not missing else "INCOMPLETE",
        "lanes": lanes,
    }


def evaluate_hard_gates(analysis: dict[str, Any], coverage: dict[str, Any], biometric_required: bool) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []
    for item in analysis.get("cross_source_consistency", []):
        if item.get("status") == "FAIL" and item.get("field") in CRITICAL_CONSISTENCY_FIELDS:
            gates.append({"gate": "CRITICAL_CROSS_SOURCE_CONTRADICTION", "triggered": True, "severity": "CRITICAL", "evidence": f"cross_source.{item['field']}", "reason": item["reason"]})
    intelligence = analysis.get("threat_intelligence", {})
    if intelligence.get("result") in {"DOCUMENT_BLACKLISTED", "IDENTITY_WATCHLIST_MATCH"}:
        gates.append({"gate": "LOCAL_PROTOTYPE_WATCHLIST_HIT", "triggered": True, "severity": "CRITICAL", "evidence": "threat_intelligence.local_lookup", "reason": intelligence.get("reason")})
    biometric = analysis.get("biometric_verification", {})
    if biometric_required and biometric.get("decision") == "MISMATCH":
        gates.append({"gate": "REQUIRED_BIOMETRIC_MISMATCH", "triggered": True, "severity": "CRITICAL", "evidence": "biometrics.face_verify", "reason": biometric.get("reason")})
    expired = next((rule for rule in analysis.get("document_rules", []) if rule.get("rule_id") == "date.expiry.current" and rule.get("status") == "FAIL"), None)
    if expired:
        gates.append({"gate": "EXPIRED_DOCUMENT", "triggered": True, "severity": "HIGH", "evidence": "document.validation.date.expiry.current", "reason": expired["reason"]})
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
