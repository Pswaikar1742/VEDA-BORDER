import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from app.benchmark import BenchmarkManifest, CaptureDegradationType, SpecimenKind, TransformationType
from tools.generate_synthetic_benchmark import generate


def test_benchmark_provenance_schema_and_real_images(tmp_path: Path):
    root = tmp_path / "benchmark"
    manifest = generate(root)
    parsed = BenchmarkManifest.model_validate_json((root / "manifest.json").read_text())
    assert len(parsed.records) == 25
    assert all(record.transformation_derived_ground_truth for record in parsed.records)
    assert all(not record.contains_real_pii for record in parsed.records)
    for record in parsed.records:
        payload = (root / record.relative_path).read_bytes()
        assert record.sha256 == hashlib.sha256(payload).hexdigest()
        with Image.open(root / record.relative_path) as image:
            assert image.format == record.format
            assert image.size == (1800, 1100)


def test_clean_variant_pairing_and_authorized_transformations(tmp_path: Path):
    manifest = generate(tmp_path / "benchmark")
    clean_ids = {record.specimen_id for record in manifest.records if record.kind == SpecimenKind.CLEAN}
    variants = [record for record in manifest.records if record.kind == SpecimenKind.CONTROLLED_VARIANT]
    capture = [record for record in manifest.records if record.kind == SpecimenKind.CAPTURE_DEGRADATION]
    assert len(clean_ids) == 4
    assert len(variants) == 16
    assert len(capture) == 5
    assert all(record.parent_specimen_id in clean_ids for record in variants + capture)
    assert {record.transformations[0].type for record in variants} == set(TransformationType)
    assert {record.transformations[0].type for record in capture} == set(CaptureDegradationType)
    assert all(record.transformations[0].bounding_box for record in variants + capture)
    assert all(record.expected_evidence_condition["condition"] == "CONTROLLED_VISIBLE_REGION_CHANGE" for record in variants)
    assert all(record.expected_evidence_condition["identity_truth_changed"] is False for record in capture)


def test_hashes_and_specimen_ids_are_unique(tmp_path: Path):
    manifest = generate(tmp_path / "benchmark")
    assert len({record.specimen_id for record in manifest.records}) == len(manifest.records)
    assert len({record.sha256 for record in manifest.records}) == len(manifest.records)


def test_regeneration_is_byte_identical(tmp_path: Path):
    first, second, different = tmp_path / "first", tmp_path / "second", tmp_path / "different"
    generate(first, seed=77)
    generate(second, seed=77)
    different_manifest = generate(different, seed=78)
    first_files = sorted(path.relative_to(first) for path in first.rglob("*") if path.is_file())
    second_files = sorted(path.relative_to(second) for path in second.rglob("*") if path.is_file())
    assert first_files == second_files
    assert [(path, (first / path).read_bytes()) for path in first_files] == [(path, (second / path).read_bytes()) for path in second_files]
    assert next(record.sha256 for record in different_manifest.records if record.specimen_id == "clean-001") != hashlib.sha256((first / "specimens/clean-001.png").read_bytes()).hexdigest()


def test_controlled_variants_change_only_logged_region(tmp_path: Path):
    root = tmp_path / "benchmark"
    manifest = generate(root)
    by_id = {record.specimen_id: record for record in manifest.records}
    for record in manifest.records:
        if record.kind != SpecimenKind.CONTROLLED_VARIANT:
            continue
        with Image.open(root / by_id[record.parent_specimen_id].relative_path) as parent, Image.open(root / record.relative_path) as variant:
            difference = ImageChops.difference(parent.convert("RGB"), variant.convert("RGB")).getbbox()
        assert difference is not None
        allowed = record.transformations[0].bounding_box
        assert difference[0] >= allowed[0] and difference[1] >= allowed[1]
        assert difference[2] <= allowed[2] and difference[3] <= allowed[3]


def test_ground_truth_is_detector_independent(tmp_path: Path):
    manifest = generate(tmp_path / "benchmark")
    serialized = json.dumps(manifest.model_dump(mode="json")).lower()
    assert "prediction" not in serialized
    assert all(record.generation_seed == manifest.seed for record in manifest.records)
    assert all(record.expected_evidence_condition.get("detector_must_be_independent", True) for record in manifest.records)
