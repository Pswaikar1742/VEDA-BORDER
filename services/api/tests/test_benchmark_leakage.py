import csv
from pathlib import Path
import pytest
from app.external_benchmarks.sidtd_adapter import SIDTDAdapter
from app.external_benchmarks.dlc2021_adapter import DLC2021Adapter
from app.external_benchmarks.fantasyid_adapter import FantasyIDAdapter


def test_sidtd_split_normal_no_leakage():
    """Verify that SIDTD official split_normal partitions have zero overlapping sample IDs."""
    splits_dir = Path("data/external/sidtd/splits/split_normal")
    if not splits_dir.is_dir():
        pytest.skip("SIDTD split_normal not available locally.")

    train_file = splits_dir / "train_split_SIDTD.csv"
    val_file = splits_dir / "val_split_SIDTD.csv"
    test_file = splits_dir / "test_split_SIDTD.csv"

    assert train_file.is_file()
    assert val_file.is_file()
    assert test_file.is_file()

    def get_paths(fpath):
        paths = set()
        with open(fpath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                paths.add(row["image_path"].strip())
        return paths

    train_paths = get_paths(train_file)
    val_paths = get_paths(val_file)
    test_paths = get_paths(test_file)

    assert len(train_paths) > 0
    assert len(val_paths) > 0
    assert len(test_paths) > 0

    # Test exact set disjointness
    train_val_overlap = train_paths.intersection(val_paths)
    train_test_overlap = train_paths.intersection(test_paths)
    val_test_overlap = val_paths.intersection(test_paths)

    assert len(train_val_overlap) == 0, f"Train and Val overlap: {train_val_overlap}"
    assert len(train_test_overlap) == 0, f"Train and Test overlap: {train_test_overlap}"
    assert len(val_test_overlap) == 0, f"Val and Test overlap: {val_test_overlap}"


def test_sidtd_adapter_record_normalization():
    """Verify SIDTD adapter produces properly normalized benchmark records without ground truth leakage."""
    adapter = SIDTDAdapter("data/external/sidtd")
    if not adapter.is_available():
        pytest.skip("SIDTD test split CSV not found.")

    samples = adapter.list_samples("test")
    assert len(samples) == 222
    for s in samples:
        assert s.benchmark_id == "SIDTD"
        assert s.ground_truth_class in {"BONAFIDE", "FORGERY"}
        assert s.document_family in {"TRAVEL_DOCUMENT", "NATIONAL_ID", "DRIVING_LICENCE"}
        assert s.split == "test"
        assert s.document_id is not None and len(s.document_id) > 0


def test_dlc2021_adapter_normalization():
    """Verify DLC-2021 adapter produces normalized attack vs bonafide records."""
    adapter = DLC2021Adapter("data/external/dlc-2021")
    if not adapter.is_available():
        pytest.skip("DLC-2021 index CSV not found.")

    samples = adapter.list_samples("all")
    assert len(samples) == 1424
    classes = {s.ground_truth_class for s in samples}
    assert classes == {"BONAFIDE", "PRESENTATION_ATTACK"}

    attack_types = {s.manipulation_type for s in samples}
    assert attack_types == {"original_mock", "grayscale_copy", "color_copy", "screen_recapture"}


def test_fantasyid_adapter_structure():
    """Verify FantasyID adapter exposes correct benchmark identifiers and split definitions."""
    adapter = FantasyIDAdapter("data/external/fantasyid")
    assert adapter.benchmark_id == "FantasyID"
    assert "hindi_subset" in adapter.list_splits()


def test_midv2020_adapter_normalization():
    """Verify MIDV-2020 adapter produces normalized records with field annotations."""
    from app.external_benchmarks.midv2020_adapter import MIDV2020Adapter

    adapter = MIDV2020Adapter("data/external/midv-2020")
    if not adapter.is_available():
        pytest.skip("MIDV-2020 not downloaded locally.")

    samples = adapter.list_samples("templates")
    assert len(samples) == 1000
    for s in samples[:20]:
        assert s.benchmark_id == "MIDV-2020"
        assert s.ground_truth_class == "BONAFIDE"
        assert s.document_family in {"TRAVEL_DOCUMENT", "NATIONAL_ID"}
        assert len(s.document_id) > 0
        assert "fields" in s.annotations
