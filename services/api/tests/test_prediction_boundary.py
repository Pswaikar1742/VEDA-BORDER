import inspect
from pathlib import Path
from app.extraction import LocalOcrAdapter
from app.integrated_pipeline import analyze_integrated
from app.visual_forensics import LocalDeterministicVisualForensics


def test_runtime_pipeline_signature_has_no_ground_truth():
    """Verify runtime pipeline functions accept ONLY specimen/selfie bytes and no ground truth."""
    sig = inspect.signature(analyze_integrated)
    param_names = list(sig.parameters.keys())
    assert "specimen_bytes" in param_names

    for forbidden in ["label", "ground_truth", "target", "annotation", "is_fake", "class_name", "split", "expected"]:
        assert forbidden not in param_names, f"Forbidden ground truth parameter '{forbidden}' found in analyze_integrated!"


def test_visual_forensics_signature_has_no_ground_truth():
    """Verify visual forensics detector operates strictly on raw image pixels."""
    detector = LocalDeterministicVisualForensics()
    sig = inspect.signature(detector.analyze)
    param_names = list(sig.parameters.keys())
    assert param_names == ["image_bytes"]


def test_local_ocr_signature_has_no_ground_truth():
    """Verify OCR adapter takes only raw image pixels."""
    adapter = LocalOcrAdapter()
    sig = inspect.signature(adapter.extract_text)
    param_names = list(sig.parameters.keys())
    assert param_names == ["specimen_bytes"]
