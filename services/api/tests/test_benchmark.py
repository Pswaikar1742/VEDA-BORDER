import hashlib
import json
from pathlib import Path

from app.benchmark import BenchmarkManifest, SpecimenKind, TransformationType
from tools.generate_synthetic_benchmark import generate


def test_benchmark_provenance_and_schema(tmp_path: Path):
    manifest = generate(tmp_path / "benchmark")
    parsed = BenchmarkManifest.model_validate_json((tmp_path / "benchmark" / "manifest.json").read_text())
    assert len(parsed.records) == 20
    assert all(record.transformation_derived_ground_truth for record in parsed.records)
    assert all(not record.contains_real_pii for record in parsed.records)
    assert all(record.sha256 == hashlib.sha256((tmp_path / "benchmark" / record.relative_path).read_bytes()).hexdigest() for record in parsed.records)


def test_clean_variant_pairing_and_authorized_transformations(tmp_path: Path):
    manifest = generate(tmp_path / "benchmark")
    clean_ids = {record.specimen_id for record in manifest.records if record.kind == SpecimenKind.CLEAN}
    variants = [record for record in manifest.records if record.kind == SpecimenKind.CONTROLLED_VARIANT]
    assert len(clean_ids) == 4
    assert all(record.parent_specimen_id in clean_ids for record in variants)
    assert {record.transformations[0].type for record in variants} == set(TransformationType)
    assert all(record.transformations and record.expected_evidence_condition["condition"] == "CONTROLLED_MISMATCH" for record in variants)


def test_hashes_and_specimen_ids_are_unique(tmp_path: Path):
    manifest = generate(tmp_path / "benchmark")
    assert len({record.specimen_id for record in manifest.records}) == len(manifest.records)
    assert len({record.sha256 for record in manifest.records}) == len(manifest.records)


def test_regeneration_is_byte_identical(tmp_path: Path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate(first, seed=77)
    generate(second, seed=77)
    first_files = sorted(path.relative_to(first) for path in first.rglob("*") if path.is_file())
    second_files = sorted(path.relative_to(second) for path in second.rglob("*") if path.is_file())
    assert first_files == second_files
    assert [(path, (first / path).read_bytes()) for path in first_files] == [(path, (second / path).read_bytes()) for path in second_files]


def test_ground_truth_is_not_detector_output(tmp_path: Path):
    manifest = generate(tmp_path / "benchmark")
    assert all(record.expected_evidence_condition.get("detector_must_be_independent", True) for record in manifest.records)
    assert all("prediction" not in json.dumps(record.model_dump(mode="json")).lower() for record in manifest.records)

