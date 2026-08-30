from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Mapping

from app.contracts import EvidenceState
from app.extraction import normalize_date


CONSISTENCY_FIELDS = ("holder_name", "document_number", "nationality", "date_of_birth", "sex", "expiry_date")


@dataclass(frozen=True)
class ContradictionPolicy:
    severity_by_field: Mapping[str, str] = field(default_factory=lambda: {
        "holder_name": "CRITICAL",
        "document_number": "CRITICAL",
        "date_of_birth": "CRITICAL",
        "expiry_date": "HIGH",
        "nationality": "HIGH",
        "sex": "HIGH",
    })


def normalize_for_comparison(field_name: str, value: str | None) -> str | None:
    if value is None or not str(value).strip():
        return None
    text = str(value).strip()
    if field_name in {"date_of_birth", "expiry_date"}:
        return normalize_date(text)
    if field_name == "holder_name":
        return " ".join(re.findall(r"[A-Z0-9]+", text.upper().replace("<", " ")))
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def compare_viz_mrz(viz: Mapping[str, str], mrz: Mapping[str, str], policy: ContradictionPolicy | None = None) -> list[dict[str, str | None]]:
    policy = policy or ContradictionPolicy()
    comparisons: list[dict[str, str | None]] = []
    for field_name in CONSISTENCY_FIELDS:
        value_a = normalize_for_comparison(field_name, viz.get(field_name))
        value_b = normalize_for_comparison(field_name, mrz.get(field_name))
        if value_a is None or value_b is None:
            missing = "VIZ and MRZ" if value_a is None and value_b is None else ("VIZ" if value_a is None else "MRZ")
            status, severity = EvidenceState.UNAVAILABLE.value, "HIGH"
            reason = f"{field_name.replace('_', ' ').title()} comparison unavailable because {missing} value is missing."
        elif value_a == value_b:
            status, severity = EvidenceState.PASS.value, "INFO"
            reason = f"Visible {field_name.replace('_', ' ')} agrees with MRZ {field_name.replace('_', ' ')}."
        else:
            status, severity = EvidenceState.FAIL.value, policy.severity_by_field[field_name]
            reason = f"Visible {field_name.replace('_', ' ')} conflicts with MRZ {field_name.replace('_', ' ')}."
        comparisons.append({
            "field": field_name,
            "source_a": "VIZ",
            "value_a": value_a,
            "source_b": "MRZ",
            "value_b": value_b,
            "status": status,
            "severity": severity,
            "reason": reason,
        })
    return comparisons
