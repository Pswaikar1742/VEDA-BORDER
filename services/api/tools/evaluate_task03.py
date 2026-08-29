#!/usr/bin/env python3
"""Evaluate predictions first; load benchmark truth only after prediction."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.pipeline import analyze_specimen


def normalized(value: str | None) -> str:
    return "".join((value or "").casefold().split())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("data/synthetic_benchmark"))
    parser.add_argument("--output", type=Path, default=Path("data/synthetic_benchmark/task03_evaluation.json"))
    args = parser.parse_args()
    specimen_paths = sorted((args.dataset / "specimens").glob("*.json"))
    predictions = {path.stem: analyze_specimen(path.read_bytes(), path.name) for path in specimen_paths}
    truth = json.loads((args.dataset / "manifest.json").read_text(encoding="utf-8"))
    by_id = {record["specimen_id"]: record for record in truth["records"]}
    fields = ("holder_name", "document_number", "nationality", "date_of_birth", "expiry_date", "sex")
    exact = normalized_scores = mrz_scores = 0
    total_fields = len(predictions) * len(fields)
    mrz_total = len(predictions) * 5
    failures: list[dict[str, str]] = []
    extraction_failures = 0
    for specimen_id, prediction in predictions.items():
        record = by_id[specimen_id]
        actual = prediction["extraction"]["visible_fields"]
        expected = record["expected_visible_fields"]
        missing = any(not actual.get(field) for field in fields)
        extraction_failures += int(missing)
        for field in fields:
            if actual.get(field) == expected.get(field): exact += 1
            if normalized(actual.get(field)) == normalized(expected.get(field)): normalized_scores += 1
            if actual.get(field) != expected.get(field): failures.append({"specimen_id": specimen_id, "field": field, "expected": expected.get(field), "observed": actual.get(field) or ""})
        observed_checks = prediction["mrz"]["checks"]
        for check in ("document_number_check", "birth_date_check", "expiry_date_check", "optional_data_check", "composite_check"):
            mrz_scores += int(observed_checks.get(check) == "PASS")
    report = {"dataset_id": truth["dataset_id"], "specimen_count": len(predictions), "ocr_field_exact_match_accuracy": exact / total_fields if total_fields else 0.0, "ocr_normalized_field_accuracy": normalized_scores / total_fields if total_fields else 0.0, "mrz_check_digit_validation_accuracy": mrz_scores / mrz_total if mrz_total else 0.0, "mrz_field_accuracy": sum(all(predictions[s]["mrz"]["fields"].get(k) == by_id[s]["expected_mrz_fields"].get(k) for k in by_id[s]["expected_mrz_fields"]) for s in predictions) / len(predictions) if predictions else 0.0, "extraction_failure_rate": extraction_failures / len(predictions) if predictions else 0.0, "per_field_failures": failures}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
