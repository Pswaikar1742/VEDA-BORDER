from typing import Any

from app.extraction import extract_specimen
from app.consistency import compare_viz_mrz
from app.intelligence import MockBorderIntelligenceAdapter, ThreatIntelligenceAdapter
from app.mrz import parse_mrz
from app.validation import validate_document


def analyze_specimen(specimen_bytes: bytes, intelligence_adapter: ThreatIntelligenceAdapter | None = None) -> dict[str, Any]:
    extracted = extract_specimen(specimen_bytes)
    mrz = parse_mrz(extracted["raw_mrz_text"])
    mrz_payload = {"mrz_detected": mrz.detected, "fields": mrz.fields, "checks": mrz.checks, "raw_lines": mrz.raw_lines, "error": mrz.error}
    consistency = compare_viz_mrz(extracted["visible_fields"], mrz.fields)
    adapter = intelligence_adapter or MockBorderIntelligenceAdapter()
    intelligence = adapter.check(extracted["visible_fields"].get("document_number"), extracted["visible_fields"].get("holder_name"))
    return {"extraction": extracted, "mrz": mrz_payload, "document_rules": validate_document(extracted["visible_fields"], mrz), "cross_source_consistency": consistency, "threat_intelligence": intelligence}
