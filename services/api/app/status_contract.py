from __future__ import annotations

from typing import Any


def _item(module: str, status: str, summary: str, severity: str = "INFO", evidence_ids: list[str] | None = None, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"module": module, "status": status, "summary": summary, "severity": severity,
            "evidence_ids": evidence_ids or [], "details": details or {}}


def build_module_statuses(analysis: dict[str, Any], family: str | None = None, selfie_supplied: bool = False) -> list[dict[str, Any]]:
    extraction = analysis.get("extraction") or {}
    fields = extraction.get("visible_fields") or {}
    missing = extraction.get("missing_fields") or []
    ocr_error = (extraction.get("ocr_metadata") or {}).get("error")
    ocr_status = "PASS" if fields and not missing and not ocr_error else "UNAVAILABLE"
    mrz = analysis.get("mrz") or {}
    applicable = mrz.get("applicability") != "NOT_APPLICABLE" and family != "VISA_OR_PERMIT" and family != "NATIONAL_ID" and family != "DRIVING_LICENCE"
    if not applicable:
        mrz_status = "NOT_APPLICABLE"
    elif not mrz.get("mrz_detected"):
        mrz_status = "UNAVAILABLE"
    else:
        mrz_status = "FAIL" if any(v == "FAIL" for v in (mrz.get("checks") or {}).values()) else "PASS"
    rules = analysis.get("document_rules") or []
    rules_status = "FAIL" if any(r.get("status") == "FAIL" for r in rules) else ("PASS" if rules and all(r.get("status") == "PASS" for r in rules) else "UNAVAILABLE")
    comparisons = analysis.get("cross_source_consistency") or []
    if not applicable:
        consistency_status = "NOT_APPLICABLE"
    elif not comparisons or any(i.get("status") == "UNAVAILABLE" for i in comparisons):
        consistency_status = "UNAVAILABLE"
    elif any(i.get("status") == "FAIL" for i in comparisons):
        consistency_status = "FAIL"
    else:
        consistency_status = "PASS"
    visual = analysis.get("visual_forensics") or {}
    visual_status = visual.get("status") if visual.get("status") in {"PASS", "FAIL", "SUSPICIOUS"} else "UNAVAILABLE"
    bio = analysis.get("biometric_verification") or {}
    bio_status = bio.get("status") if selfie_supplied and bio.get("status") in {"PASS", "FAIL", "SUSPICIOUS"} else ("NOT_APPLICABLE" if not selfie_supplied else "UNAVAILABLE")
    intel = analysis.get("threat_intelligence") or {}
    intel_status = intel.get("status") if intel.get("status") in {"PASS", "FAIL", "SUSPICIOUS"} else "UNAVAILABLE"
    linkage = analysis.get("identity_linkage") or {}
    linkage_status = linkage.get("status") if linkage.get("status") in {"PASS", "FAIL", "SUSPICIOUS"} else "UNAVAILABLE"
    return [
        _item("capture_quality", "PASS" if (analysis.get("capture_quality") or {}).get("acceptable") else "FAIL", "Capture quality is sufficient for local analysis." if (analysis.get("capture_quality") or {}).get("acceptable") else "Capture quality is too poor to trust downstream evidence.", "INFO" if (analysis.get("capture_quality") or {}).get("acceptable") else "HIGH", ["capture.quality"]),
        _item("ocr_viz", ocr_status, "Required visible identity fields were extracted." if ocr_status == "PASS" else "Required visible identity fields are incomplete or unavailable.", "INFO" if ocr_status == "PASS" else "HIGH", ["document.extraction.result"], {"missing_fields": missing}),
        _item("mrz", mrz_status, "MRZ parsed and deterministic check digits passed." if mrz_status == "PASS" else ("MRZ check digits failed." if mrz_status == "FAIL" else ("MRZ is not applicable to this family." if mrz_status == "NOT_APPLICABLE" else "No machine-readable zone was detected.")), "CRITICAL" if mrz_status == "FAIL" else "INFO", ["document.mrz.result"], {"checks": mrz.get("checks", {})}),
        _item("document_rules", rules_status, "Family-aware document rules completed." if rules_status == "PASS" else "One or more required document rules failed." if rules_status == "FAIL" else "Document rules did not produce sufficient evidence.", "HIGH" if rules_status == "FAIL" else "INFO", [f"document.validation.{r.get('rule_id')}" for r in rules]),
        _item("consistency", consistency_status, "Visible and machine-readable fields agree." if consistency_status == "PASS" else "Visible and machine-readable fields contradict each other." if consistency_status == "FAIL" else "Comparison could not be performed because required source data is unavailable." if consistency_status == "UNAVAILABLE" else "Cross-source comparison is not applicable.", "CRITICAL" if consistency_status == "FAIL" else "INFO", [f"cross_source.{i.get('field')}" for i in comparisons], {"comparisons": comparisons}),
        _item("visual_forensics", visual_status, "Local image-forensic measures found no flagged region." if visual_status == "PASS" else "A suspicious image region requires review." if visual_status == "SUSPICIOUS" else "Visual-forensics lane reported a failure." if visual_status == "FAIL" else "Visual forensics is unavailable.", "HIGH" if visual_status in {"FAIL", "SUSPICIOUS"} else "INFO", ["forensics.visual"]),
        _item("biometrics", bio_status, bio.get("reason", "Face comparison completed." if bio_status == "PASS" else "Face comparison unavailable."), "CRITICAL" if bio_status == "FAIL" else "INFO", ["biometrics.face_verify"]),
        _item("watchlist", intel_status, intel.get("reason", "No local prototype watchlist match." if intel_status == "PASS" else "Local prototype watchlist unavailable."), "CRITICAL" if intel_status == "FAIL" else "INFO", ["threat_intelligence.local_lookup"], {"finding_type": intel.get("result")}),
        _item("identity_linkage", linkage_status, linkage.get("reason", "No identity-linkage finding." if linkage_status == "PASS" else "Identity linkage unavailable."), "HIGH" if linkage_status == "SUSPICIOUS" else "INFO", ["identity_linkage.local_embedding"]),
    ]
