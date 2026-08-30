#!/usr/bin/env python3
"""Freeze pixel-only predictions, then load truth and evaluate Task 04 support metrics."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.contracts import build_task04_autopsy
from app.intelligence import MockBorderIntelligenceAdapter
from app.pipeline import analyze_specimen


FIELDS = ("holder_name", "document_number", "nationality", "date_of_birth", "sex", "expiry_date")
CHECKS = ("document_number_check", "birth_date_check", "expiry_date_check", "optional_data_check", "composite_check")


def compact(value: str | None) -> str:
    return "".join((value or "").casefold().split())


def ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def group_metrics(specimen_ids: list[str], predictions: dict[str, dict[str, Any]], truth: dict[str, dict[str, Any]]) -> dict[str, Any]:
    exact = normalized = mrz_fields = check_digits = consistency_correct = 0
    extraction_failures = mrz_detected = expected_contradictions = detected_contradictions = 0
    per_field: dict[str, dict[str, int]] = defaultdict(lambda: {"exact_correct": 0, "normalized_correct": 0, "total": 0})
    failures: list[dict[str, str]] = []
    for specimen_id in specimen_ids:
        prediction, record = predictions[specimen_id], truth[specimen_id]
        actual_raw = prediction["extraction"]["raw_visible_fields"]
        actual = prediction["extraction"]["visible_fields"]
        expected_raw, expected = record["expected_visible_raw_fields"], record["expected_visible_fields"]
        extraction_failures += int(any(not actual.get(field) for field in FIELDS))
        mrz_detected += int(prediction["mrz"]["mrz_detected"])
        for field in FIELDS:
            exact_match = actual_raw.get(field) == expected_raw.get(field)
            normalized_match = compact(actual.get(field)) == compact(expected.get(field))
            exact += int(exact_match)
            normalized += int(normalized_match)
            per_field[field]["exact_correct"] += int(exact_match)
            per_field[field]["normalized_correct"] += int(normalized_match)
            per_field[field]["total"] += 1
            if not normalized_match:
                failures.append({"specimen_id": specimen_id, "field": field, "expected": expected.get(field, ""), "observed": actual.get(field, "")})
            mrz_fields += int(prediction["mrz"]["fields"].get(field) == record["expected_mrz_fields"].get(field))
            expected_status = "FAIL" if record["expected_contradiction"].get("expected") and record["expected_contradiction"].get("field") == field else "PASS"
            observed_status = next(item["status"] for item in prediction["cross_source_consistency"] if item["field"] == field)
            consistency_correct += int(observed_status == expected_status)
        for check in CHECKS:
            check_digits += int(prediction["mrz"]["checks"].get(check) == "PASS")
        if record["expected_contradiction"].get("expected"):
            expected_contradictions += 1
            field = record["expected_contradiction"]["field"]
            detected_contradictions += int(any(item["field"] == field and item["status"] == "FAIL" for item in prediction["cross_source_consistency"]))
    visible_total = len(specimen_ids) * len(FIELDS)
    check_total = len(specimen_ids) * len(CHECKS)
    return {
        "specimen_count": len(specimen_ids),
        "visible_field_exact_match_accuracy": ratio(exact, visible_total),
        "visible_field_normalized_accuracy": ratio(normalized, visible_total),
        "per_field_accuracy": {field: {"exact": ratio(values["exact_correct"], values["total"]), "normalized": ratio(values["normalized_correct"], values["total"])} for field, values in sorted(per_field.items())},
        "mrz_detection_rate": ratio(mrz_detected, len(specimen_ids)),
        "mrz_field_accuracy": ratio(mrz_fields, visible_total),
        "mrz_check_digit_validation_accuracy": ratio(check_digits, check_total),
        "extraction_failure_rate": ratio(extraction_failures, len(specimen_ids)),
        "consistency_status_accuracy": ratio(consistency_correct, visible_total),
        "expected_contradiction_detection_rate": ratio(detected_contradictions, expected_contradictions) if expected_contradictions else None,
        "expected_contradiction_count": expected_contradictions,
        "normalized_field_failures": failures,
    }


def golden_cases(predictions: dict[str, dict[str, Any]], specimen_bytes: dict[str, bytes]) -> dict[str, Any]:
    def status(specimen_id: str, field: str) -> dict[str, Any]:
        return next(item for item in predictions[specimen_id]["cross_source_consistency"] if item["field"] == field)

    unavailable = analyze_specimen(specimen_bytes["clean-001"], MockBorderIntelligenceAdapter(available=False))
    unavailable_autopsy = build_task04_autopsy("golden-unavailable", "clean-001.png", "0" * 64, unavailable, intelligence_mandatory=True)
    return {
        "case_a_clean_consistent": {"cross_source_statuses": {item["field"]: item["status"] for item in predictions["clean-001"]["cross_source_consistency"]}, "mrz_checks": predictions["clean-001"]["mrz"]["checks"], "expiry_rule": next(rule for rule in predictions["clean-001"]["document_rules"] if rule["rule_id"] == "date.expiry.current"), "intelligence": predictions["clean-001"]["threat_intelligence"]["result"]},
        "case_b_dob_alteration": status("variant-001-02", "date_of_birth"),
        "case_c_name_alteration": status("variant-001-01", "holder_name"),
        "case_d_expiry_alteration": {"comparison": status("variant-001-03", "expiry_date"), "expiry_rule": next(rule for rule in predictions["variant-001-03"]["document_rules"] if rule["rule_id"] == "date.expiry.current")},
        "case_e_mock_blacklist": {"status": predictions["clean-004"]["threat_intelligence"]["status"], "result": predictions["clean-004"]["threat_intelligence"]["result"], "source": predictions["clean-004"]["threat_intelligence"]["source"]},
        "case_f_intelligence_unavailable": {"status": unavailable["threat_intelligence"]["status"], "coverage_state": unavailable_autopsy.evidence_coverage.state, "missing_mandatory": unavailable_autopsy.evidence_coverage.missing_mandatory, "outcome": unavailable_autopsy.outcome},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("data/synthetic_benchmark"))
    parser.add_argument("--output", type=Path, default=Path("data/synthetic_benchmark/task04_evaluation.json"))
    args = parser.parse_args()

    # Runtime phase: bytes only. No manifest, IDs, filenames, parents, or labels enter analyze_specimen.
    paths = sorted(path for path in (args.dataset / "specimens").iterdir() if path.suffix.lower() in {".png", ".jpg", ".jpeg"})
    specimen_bytes = {path.stem: path.read_bytes() for path in paths}
    predictions = {specimen_id: analyze_specimen(payload) for specimen_id, payload in specimen_bytes.items()}

    # Evaluation phase begins only after every prediction above is frozen.
    manifest = json.loads((args.dataset / "manifest.json").read_text(encoding="utf-8"))
    truth = {record["specimen_id"]: record for record in manifest["records"]}
    groups = {
        "clean_images": [specimen_id for specimen_id, record in truth.items() if record["kind"] == "CLEAN"],
        "controlled_altered_images": [specimen_id for specimen_id, record in truth.items() if record["kind"] == "CONTROLLED_VARIANT"],
        "capture_degradation_images": [specimen_id for specimen_id, record in truth.items() if record["kind"] == "CAPTURE_DEGRADATION"],
        "all_images": sorted(truth),
    }
    report = {
        "dataset_id": manifest["dataset_id"],
        "metric_scope": "image extraction, MRZ parsing, deterministic validation, and consistency support only; not fraud, forgery, or authenticity accuracy",
        "prediction_boundary": "All runtime predictions were frozen from PNG/JPEG bytes before manifest ground truth was loaded.",
        "groups": {name: group_metrics(ids, predictions, truth) for name, ids in groups.items()},
        "golden_cases": golden_cases(predictions, specimen_bytes),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
