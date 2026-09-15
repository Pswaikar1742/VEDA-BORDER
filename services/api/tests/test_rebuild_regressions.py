from pathlib import Path

import pytest
from fastapi import HTTPException

from app.autopsy import build_integrated_autopsy
from app.integrated_pipeline import analyze_integrated
from app.routes.workspace import get_fixture_file
from app.extraction import extract_generic_fields
from app.preprocessing import preprocess_specimen


ROOT = Path(__file__).resolve().parents[3]


def _run(name: str, family: str = "TRAVEL_DOCUMENT"):
    data = (ROOT / "data" / "integrated_fixtures" / name).read_bytes()
    return analyze_integrated(data, manual_family=family, database_path="/tmp/veda-rebuild-tests.sqlite", enrol_identity=False)


def test_fixture_path_traversal_is_rejected():
    with pytest.raises(HTTPException) as exc:
        get_fixture_file("../../README.md")
    assert exc.value.status_code == 404


def test_mrz_failure_cannot_be_low_risk():
    analysis = _run("travel_clean.png")
    analysis["mrz"]["checks"]["document_number"] = "FAIL"
    from app.policy import build_coverage, evaluate_hard_gates, triage_outcome
    coverage = build_coverage(analysis, True, False, True)
    gates = evaluate_hard_gates(analysis, coverage, False)
    analysis["hard_gates"] = gates
    analysis["outcome"], _ = triage_outcome(analysis, gates)
    assert analysis["outcome"] != "LOW_RISK"
    assert "MRZ_CHECKSUM_FAILURE" in {gate["gate"] for gate in analysis["hard_gates"]}


def test_dob_contradiction_is_consumed_by_policy():
    analysis = _run("travel_dob_altered.png")
    assert analysis["outcome"] == "HIGH_RISK"
    assert analysis["evidence_coverage"]["lanes"][3]["evidence_status"] == "FAIL"


def test_canonical_statuses_and_artifact_dimensions_are_returned():
    analysis = _run("travel_clean.png")
    report = build_integrated_autopsy("case", "travel_clean.png", "a" * 64, analysis, False)
    modules = {item.module: item.status.value for item in report.module_statuses}
    assert modules["mrz"] == "PASS"
    assert report.artifact_metadata["analysis_image_width"] == 1800
    assert report.artifact_metadata["analysis_image_height"] == 1100


def test_generic_parser_extracts_stable_dates_and_identifier_without_guessing():
    fields, provenance = extract_generic_fields("Date of birth\n14.08.1994\nDocument No C193895647\n")
    assert fields["date_of_birth"] == "14-08-1994"
    assert fields["document_number"] == "C193895647"
    assert "holder_name" not in fields
    assert provenance["document_number"]["method"] == "layout_association"


def test_geometry_metadata_and_conservative_crop():
    data = (ROOT / "data" / "external_demo" / "MIDV2020" / "scan_rotated" / "alb_id" / "00.jpg").read_bytes()
    processed, metadata = preprocess_specimen(data)
    assert metadata["document_region_detected"] is True
    assert "DOCUMENT_REGION_CROP" in metadata["operations"]
    assert len(processed) > 0
