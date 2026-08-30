import asyncio
from pathlib import Path

from app.consistency import compare_viz_mrz, normalize_for_comparison
from app.contracts import ScreeningOutcome, build_task04_autopsy
from app.intelligence import IntelligenceResult, MockBorderIntelligenceAdapter
from app.pipeline import analyze_specimen
from app.routes.scan import scan_specimen
from tools.generate_synthetic_benchmark import generate


VIZ = {"holder_name": "ARI SOLEN", "document_number": "VDA111111", "nationality": "NSL", "date_of_birth": "17 JUN 1998", "sex": "X", "expiry_date": "2031-02-21"}
MRZ = {"holder_name": "ARI<SOLEN", "document_number": "VDA111111", "nationality": "NSL", "date_of_birth": "1998-06-17", "sex": "X", "expiry_date": "21 FEB 2031"}


def by_field(comparisons):
    return {item["field"]: item for item in comparisons}


def test_clean_viz_mrz_consistency_and_normalization():
    result = by_field(compare_viz_mrz(VIZ, MRZ))
    assert all(item["status"] == "PASS" for item in result.values())
    assert normalize_for_comparison("date_of_birth", "18 JUN 1998") == "1998-06-18"
    assert normalize_for_comparison("holder_name", "  Ari<<<Solen ") == "ARI SOLEN"
    assert normalize_for_comparison("document_number", "vda-111 111") == "VDA111111"


def test_dob_name_and_expiry_mismatch_detection():
    dob = by_field(compare_viz_mrz({**VIZ, "date_of_birth": "1993-06-17"}, MRZ))["date_of_birth"]
    name = by_field(compare_viz_mrz({**VIZ, "holder_name": "LIO MAREN"}, MRZ))["holder_name"]
    expiry = by_field(compare_viz_mrz({**VIZ, "expiry_date": "2021-02-21"}, MRZ))["expiry_date"]
    assert (dob["status"], dob["severity"], dob["value_a"], dob["value_b"]) == ("FAIL", "CRITICAL", "1993-06-17", "1998-06-17")
    assert (name["status"], name["severity"]) == ("FAIL", "CRITICAL")
    assert (expiry["status"], expiry["severity"]) == ("FAIL", "HIGH")


def test_missing_viz_and_missing_mrz_are_unavailable():
    missing_viz = by_field(compare_viz_mrz({key: value for key, value in VIZ.items() if key != "sex"}, MRZ))["sex"]
    missing_mrz = by_field(compare_viz_mrz(VIZ, {key: value for key, value in MRZ.items() if key != "nationality"}))["nationality"]
    assert missing_viz["status"] == "UNAVAILABLE"
    assert missing_mrz["status"] == "UNAVAILABLE"


def test_mock_intelligence_clear_hit_identity_and_unavailable():
    adapter = MockBorderIntelligenceAdapter()
    clear = adapter.check("VDA111111", "ARI SOLEN")
    hit = adapter.check("VDA444444", "NERA VALE")
    identity = adapter.check("VDA111111", "WATCH DEMO")
    unavailable = MockBorderIntelligenceAdapter(available=False).check("VDA444444", "NERA VALE")
    assert (clear["status"], clear["result"]) == ("PASS", IntelligenceResult.CLEAR.value)
    assert (hit["status"], hit["result"]) == ("FAIL", IntelligenceResult.DOCUMENT_BLACKLISTED.value)
    assert identity["result"] == IntelligenceResult.IDENTITY_WATCHLIST_MATCH.value
    assert identity["lookups"][0]["queried_synthetic_identifier"] == "WATCH DEMO"
    assert unavailable["status"] == IntelligenceResult.UNAVAILABLE.value
    assert all(item["source"] == "MOCK_BORDER_INTELLIGENCE" and item["demo_mock"] for result in (clear, hit, identity, unavailable) for item in result["lookups"])


def test_pixel_ocr_detects_controlled_contradictions_and_blacklist(tmp_path: Path):
    root = tmp_path / "benchmark"
    generate(root)
    clean = analyze_specimen((root / "specimens/clean-001.png").read_bytes())
    dob = analyze_specimen((root / "specimens/variant-001-02.png").read_bytes())
    name = analyze_specimen((root / "specimens/variant-001-01.png").read_bytes())
    expiry = analyze_specimen((root / "specimens/variant-001-03.png").read_bytes())
    blacklisted = analyze_specimen((root / "specimens/clean-004.png").read_bytes())
    assert all(item["status"] == "PASS" for item in clean["cross_source_consistency"])
    assert by_field(dob["cross_source_consistency"])["date_of_birth"]["status"] == "FAIL"
    assert by_field(name["cross_source_consistency"])["holder_name"]["status"] == "FAIL"
    assert by_field(expiry["cross_source_consistency"])["expiry_date"]["status"] == "FAIL"
    assert blacklisted["threat_intelligence"]["result"] == "DOCUMENT_BLACKLISTED"


def test_ocr_reads_pixels_not_filename_or_manifest(tmp_path: Path):
    root = tmp_path / "benchmark"
    generate(root)
    clean_bytes = (root / "specimens/clean-001.png").read_bytes()
    changed_bytes = (root / "specimens/variant-001-01.png").read_bytes()
    clean = analyze_specimen(clean_bytes)
    changed = analyze_specimen(changed_bytes)
    assert clean_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    assert changed_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    assert clean["extraction"]["visible_fields"]["holder_name"] == "ARI SOLEN"
    assert changed["extraction"]["visible_fields"]["holder_name"] == "LIO MAREN"
    assert clean["mrz"]["fields"]["holder_name"] == changed["mrz"]["fields"]["holder_name"] == "ARI SOLEN"


def test_coverage_governor_preserves_unavailable_semantics(tmp_path: Path):
    root = tmp_path / "benchmark"
    generate(root)
    analysis = analyze_specimen((root / "specimens/clean-001.png").read_bytes(), MockBorderIntelligenceAdapter(available=False))
    autopsy = build_task04_autopsy("scan", "demo.png", "a" * 64, analysis, intelligence_mandatory=True)
    assert autopsy.outcome == ScreeningOutcome.INDETERMINATE
    assert "threat_intelligence" in autopsy.evidence_coverage.missing_mandatory
    assert "forensics.visual_tamper" in autopsy.evidence_coverage.missing_mandatory
    assert "biometrics.face_verify" in autopsy.evidence_coverage.missing_mandatory
    assert any(lane.lane_id == "electronic_credential.nfc" and lane.status.value == "UNAVAILABLE" for lane in autopsy.evidence_lanes)
    assert autopsy.evidence_coverage.state == "INCOMPLETE"


def test_png_upload_returns_task04_autopsy_sections(tmp_path: Path):
    root = tmp_path / "benchmark"
    generate(root)

    class Upload:
        filename = "renamed-demo.png"
        content_type = "image/png"

        async def read(self):
            return (root / "specimens/variant-001-02.png").read_bytes()

    result = asyncio.run(scan_specimen(Upload())).model_dump(mode="json")
    assert result["visible_document_data"]["visible_fields"]["date_of_birth"] == "1991-06-18"
    assert next(item for item in result["cross_source_consistency"] if item["field"] == "date_of_birth")["status"] == "FAIL"
    assert result["threat_intelligence"]["source"] == "MOCK_BORDER_INTELLIGENCE"
    assert result["outcome"] == "INDETERMINATE"
    evidence_ids = {item["evidence_id"] for lane in result["evidence_lanes"] for item in lane["evidence_items"]}
    assert set(result["outcome_reasons"]) <= evidence_ids
