from typing import Any

from app.extraction import extract_specimen
from app.mrz import parse_mrz
from app.validation import validate_document


def analyze_specimen(specimen_bytes: bytes, filename: str | None = None) -> dict[str, Any]:
    extracted = extract_specimen(specimen_bytes, filename)
    mrz = parse_mrz(extracted["raw_ocr_text"])
    return {"extraction": extracted, "mrz": {"mrz_detected": mrz.detected, "fields": mrz.fields, "checks": mrz.checks, "raw_lines": mrz.raw_lines, "error": mrz.error}, "document_rules": validate_document(extracted["visible_fields"], mrz)}

