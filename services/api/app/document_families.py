from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.contracts import DocumentFamily


@dataclass(frozen=True)
class DocumentFamilyAdapter:
    family: DocumentFamily
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    supports_mrz: bool
    portrait_region: tuple[float, float, float, float]

    def applicability(self) -> dict[str, str]:
        return {
            "mrz": "APPLICABLE" if self.supports_mrz else "NOT_APPLICABLE",
            "electronic_credential": "FUTURE_INTERFACE" if self.family == DocumentFamily.TRAVEL_DOCUMENT else "NOT_APPLICABLE",
        }


ADAPTERS: dict[DocumentFamily, DocumentFamilyAdapter] = {
    DocumentFamily.TRAVEL_DOCUMENT: DocumentFamilyAdapter(
        DocumentFamily.TRAVEL_DOCUMENT,
        ("holder_name", "document_number", "nationality", "date_of_birth", "sex", "expiry_date"),
        (),
        True,
        (0.055, 0.245, 0.260, 0.690),
    ),
    DocumentFamily.VISA_OR_PERMIT: DocumentFamilyAdapter(
        DocumentFamily.VISA_OR_PERMIT,
        ("holder_name", "document_number", "nationality", "date_of_birth", "expiry_date"),
        ("sex",),
        False,
        (0.055, 0.245, 0.260, 0.690),
    ),
    DocumentFamily.NATIONAL_ID: DocumentFamilyAdapter(
        DocumentFamily.NATIONAL_ID,
        ("holder_name", "document_number", "date_of_birth"),
        ("nationality", "sex", "expiry_date"),
        False,
        (0.055, 0.245, 0.260, 0.690),
    ),
    DocumentFamily.DRIVING_LICENCE: DocumentFamilyAdapter(
        DocumentFamily.DRIVING_LICENCE,
        ("holder_name", "document_number", "date_of_birth", "expiry_date"),
        ("nationality", "sex"),
        False,
        (0.055, 0.245, 0.260, 0.690),
    ),
}


def get_adapter(family: str | DocumentFamily) -> DocumentFamilyAdapter:
    try:
        key = family if isinstance(family, DocumentFamily) else DocumentFamily(family)
    except ValueError as exc:
        raise ValueError(f"Unsupported document family: {family}") from exc
    return ADAPTERS[key]


def classify_document(raw_text: str, manual_override: str | None = None) -> dict[str, Any]:
    if manual_override:
        adapter = get_adapter(manual_override)
        return {"family": adapter.family.value, "method": "MANUAL_OVERRIDE", "confidence": None}
    upper = raw_text.upper()
    compact = "".join(upper.split())
    markers = {
        DocumentFamily.TRAVEL_DOCUMENT: ("MACHINEREADABLEZONE", "P<", "X<NSL", "VEDA-BORDERSYNTHETIC"),
        DocumentFamily.VISA_OR_PERMIT: ("VISAORPERMIT", "VISA", "PERMIT"),
        DocumentFamily.NATIONAL_ID: ("NATIONALID", "IDENTITYCARD"),
        DocumentFamily.DRIVING_LICENCE: ("DRIVINGLICENCE", "DRIVERLICENCE"),
    }
    scores = {family: sum(marker in compact for marker in family_markers) for family, family_markers in markers.items()}
    family = max(scores, key=scores.get)
    if scores[family] == 0:
        family = DocumentFamily.TRAVEL_DOCUMENT
        return {"family": family.value, "method": "LAYOUT_FALLBACK", "confidence": None}
    return {"family": family.value, "method": "PIXEL_OCR_MARKERS", "confidence": round(min(0.99, 0.62 + 0.12 * scores[family]), 2)}
