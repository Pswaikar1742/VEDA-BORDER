import json
from pathlib import Path

from app.mrz import check_digit, decode_date, parse_mrz
from app.pipeline import analyze_specimen
from tools.generate_synthetic_benchmark import generate


def test_known_icao_check_digits():
    assert check_digit("L898902C<") == "3"
    assert check_digit("740812") == "2"
    assert check_digit("120415") == "9"


def test_generated_mrzs_parse_and_validate(tmp_path: Path):
    manifest = generate(tmp_path / "benchmark")
    for record in manifest.records:
        payload = json.loads((tmp_path / "benchmark" / record.relative_path).read_text())
        result = parse_mrz(payload["visible_text"])
        assert result.detected is True
        assert set(result.checks.values()) == {"PASS"}
        assert result.fields["document_number"] == payload["mrz_document_number"]


def test_visible_variants_preserve_parent_mrz(tmp_path: Path):
    manifest = generate(tmp_path / "benchmark")
    payloads = {record.specimen_id: json.loads((tmp_path / "benchmark" / record.relative_path).read_text()) for record in manifest.records}
    for record in manifest.records:
        if record.parent_specimen_id:
            parent = payloads[record.parent_specimen_id]
            variant = payloads[record.specimen_id]
            assert variant["mrz_line_1"] == parent["mrz_line_1"]
            assert variant["mrz_line_2"] == parent["mrz_line_2"]


def test_mrz_malformed_and_bad_check_digit(tmp_path: Path):
    assert parse_mrz("not an mrz").detected is False
    manifest = generate(tmp_path / "benchmark")
    payload = json.loads((tmp_path / "benchmark" / manifest.records[0].relative_path).read_text())
    bad_line2 = payload["mrz_line_2"][:9] + ("9" if payload["mrz_line_2"][9] != "9" else "8") + payload["mrz_line_2"][10:]
    result = parse_mrz(payload["mrz_line_1"] + "\n" + bad_line2)
    assert result.detected is True
    assert result.checks["document_number_check"] == "FAIL"


def test_date_rules_and_required_fields(tmp_path: Path):
    generate(tmp_path / "benchmark")
    payload = json.loads((tmp_path / "benchmark/specimens/clean-001.json").read_text())
    analysis = analyze_specimen(json.dumps(payload, sort_keys=True).encode(), "arbitrary-name.json")
    rules = {rule["rule_id"]: rule for rule in analysis["document_rules"]}
    assert decode_date("940317") == "1994-03-17"
    assert rules["fields.required"]["status"] == "PASS"
    assert rules["date.expiry.after_birth"]["status"] == "PASS"
    assert rules["date.birth.not_future"]["status"] == "PASS"


def test_runtime_does_not_need_manifest_or_filename_truth(tmp_path: Path):
    generate(tmp_path / "benchmark")
    specimen = next((tmp_path / "benchmark/specimens").glob("clean-001.json"))
    analysis = analyze_specimen(specimen.read_bytes(), "renamed-and-untruthful.bin")
    assert analysis["extraction"]["visible_fields"]["holder_name"] == "Ari Solen"
    assert "manifest" not in analysis["extraction"]["ocr_metadata"]
