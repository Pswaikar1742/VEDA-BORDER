from __future__ import annotations

from typing import Any


FIELD_CLAIMS = {
    "holder_name": "holder_name",
    "document_number": "document_number",
    "nationality": "nationality",
    "date_of_birth": "date_of_birth",
    "sex": "sex",
    "expiry_date": "expiry_date",
}

SOURCE_TIERS = {
    "ELECTRONIC_CREDENTIAL": 1,
    "AUTHORIZED_GOVERNMENT_SOURCE": 1,
    "MRZ": 2,
    "DOCUMENT_RULE": 2,
    "VIZ_OCR": 3,
    "VISUAL_FORENSICS": 3,
    "DOCUMENT_PORTRAIT": 3,
    "LIVE_FACE": 4,
    "BIOMETRIC_VERIFICATION": 4,
    "LOCAL_PROTOTYPE_WATCHLIST": 2,
    "BIOMETRIC_LINKAGE": 4,
}


def build_evidence_graph(analysis: dict[str, Any]) -> dict[str, Any]:
    claims = ["holder_identity", *FIELD_CLAIMS.values(), "portrait_identity", "document_integrity", "document_status"]
    nodes: list[dict[str, Any]] = [{"id": f"claim:{claim}", "type": "CLAIM", "claim": claim} for claim in dict.fromkeys(claims)]
    edges: list[dict[str, Any]] = []

    visible = analysis.get("extraction", {}).get("visible_fields", {})
    mrz = analysis.get("mrz", {}).get("fields", {})
    comparisons = {item["field"]: item for item in analysis.get("cross_source_consistency", [])}
    for field, claim in FIELD_CLAIMS.items():
        for source, values in (("VIZ_OCR", visible), ("MRZ", mrz)):
            value = values.get(field)
            node_id = f"evidence:{source}:{field}"
            nodes.append({"id": node_id, "type": "EVIDENCE", "source": source, "authority_tier": SOURCE_TIERS[source], "field": field, "normalized_value": value, "provenance": "submitted_image_pixels"})
            comparison = comparisons.get(field, {})
            if value is None:
                relation = "UNAVAILABLE"
            elif comparison.get("status") == "FAIL":
                relation = "CONTRADICTS"
            else:
                relation = "SUPPORTS"
            edges.append({"from": node_id, "to": f"claim:{claim}", "relation": relation})

    lane_map = [
        ("VISUAL_FORENSICS", "document_integrity", analysis.get("visual_forensics", {}).get("status")),
        ("BIOMETRIC_VERIFICATION", "portrait_identity", analysis.get("biometric_verification", {}).get("status")),
        ("LOCAL_PROTOTYPE_WATCHLIST", "document_status", analysis.get("threat_intelligence", {}).get("status")),
        ("BIOMETRIC_LINKAGE", "holder_identity", analysis.get("identity_linkage", {}).get("status")),
    ]
    for source, claim, status in lane_map:
        node_id = f"evidence:{source}"
        nodes.append({"id": node_id, "type": "EVIDENCE", "source": source, "authority_tier": SOURCE_TIERS[source], "status": status, "provenance": "local_runtime"})
        relation = "UNAVAILABLE" if status in {None, "UNAVAILABLE"} else ("CONTRADICTS" if status in {"FAIL", "SUSPICIOUS"} else "SUPPORTS")
        edges.append({"from": node_id, "to": f"claim:{claim}", "relation": relation})

    nodes += [
        {"id": "evidence:ELECTRONIC_CREDENTIAL", "type": "EVIDENCE", "source": "ELECTRONIC_CREDENTIAL", "authority_tier": 1, "status": "UNAVAILABLE", "provenance": "future_adapter_placeholder"},
        {"id": "evidence:AUTHORIZED_GOVERNMENT_SOURCE", "type": "EVIDENCE", "source": "AUTHORIZED_GOVERNMENT_SOURCE", "authority_tier": 1, "status": "UNAVAILABLE", "provenance": "inactive_future_interface"},
    ]
    edges += [
        {"from": "evidence:ELECTRONIC_CREDENTIAL", "to": "claim:document_status", "relation": "UNAVAILABLE"},
        {"from": "evidence:AUTHORIZED_GOVERNMENT_SOURCE", "to": "claim:document_status", "relation": "UNAVAILABLE"},
    ]
    return {"nodes": nodes, "edges": edges, "authority_policy": "Lower numeric tier has higher authority; PASS counts are not averaged and cannot cancel higher-authority contradictions."}
