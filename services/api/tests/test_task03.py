from pathlib import Path

from app.mrz import check_digit, decode_date, parse_mrz
from app.pipeline import analyze_specimen
from tools.generate_synthetic_benchmark import credential, generate


def test_known_icao_check_digits():
    assert check_digit("L898902C<") == "3"
    assert check_digit("740812") == "2"
    assert check_digit("120415") == "9"


def test_generated_image_mrzs_parse_and_validate(tmp_path: Path):
    root = tmp_path / "benchmark"
    manifest = generate(root)
    for record in manifest.records:
        result = analyze_specimen((root / record.relative_path).read_bytes())["mrz"]
        assert result["mrz_detected"] is True
        assert set(result["checks"].values()) == {"PASS"}
        assert result["fields"]["document_number"] == record.expected_mrz_fields["document_number"]


def test_visible_variants_preserve_parent_mrz_from_pixels(tmp_path: Path):
    root = tmp_path / "benchmark"
    manifest = generate(root)
    mrzs = {record.specimen_id: analyze_specimen((root / record.relative_path).read_bytes())["mrz"]["raw_lines"] for record in manifest.records}
    for record in manifest.records:
        if record.kind.value == "CONTROLLED_VARIANT":
            assert mrzs[record.specimen_id] == mrzs[record.parent_specimen_id]


def test_mrz_malformed_and_bad_check_digit():
    assert parse_mrz("not an mrz").detected is False
    payload = credential(20260829, 1)
    bad_line2 = payload["mrz_line_2"][:9] + ("9" if payload["mrz_line_2"][9] != "9" else "8") + payload["mrz_line_2"][10:]
    result = parse_mrz(payload["mrz_line_1"] + "\n" + bad_line2)
    assert result.detected is True
    assert result.checks["document_number_check"] == "FAIL"


def test_date_rules_and_required_fields_from_image(tmp_path: Path):
    root = tmp_path / "benchmark"
    generate(root)
    analysis = analyze_specimen((root / "specimens/clean-001.png").read_bytes())
    rules = {rule["rule_id"]: rule for rule in analysis["document_rules"]}
    assert decode_date("940317") == "1994-03-17"
    assert rules["fields.required"]["status"] == "PASS"
    assert rules["date.expiry.after_birth"]["status"] == "PASS"
    assert rules["date.birth.not_future"]["status"] == "PASS"


def test_runtime_does_not_need_manifest_filename_or_json_truth(tmp_path: Path, monkeypatch):
    root = tmp_path / "benchmark"
    generate(root)
    pixels = (root / "specimens/clean-001.png").read_bytes()

    def forbid_truth_reads(*args, **kwargs):
        raise AssertionError("runtime attempted to read benchmark truth")

    monkeypatch.setattr(Path, "read_text", forbid_truth_reads)
    analysis = analyze_specimen(pixels)
    assert analysis["extraction"]["visible_fields"]["holder_name"] == "ARI SOLEN"
    assert analysis["extraction"]["ocr_metadata"]["input_format"] == "PNG"
    rejected = analyze_specimen(b'{"visible_text":"HOLDER NAME: MANIFEST LEAK"}')
    assert rejected["extraction"]["visible_fields"] == {}
    assert rejected["extraction"]["ocr_metadata"]["error"]
