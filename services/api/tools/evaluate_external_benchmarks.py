from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Ensure services/api is on sys.path
CURRENT_FILE = Path(__file__).resolve()
API_ROOT = CURRENT_FILE.parent.parent
REPO_ROOT = API_ROOT.parent.parent

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import resolve_repo_path
from app.external_benchmarks.base import (
    ExternalBenchmarkSample,
    calculate_binary_classification_metrics,
)
from app.external_benchmarks.sidtd_adapter import SIDTDAdapter
from app.external_benchmarks.fantasyid_adapter import FantasyIDAdapter
from app.external_benchmarks.dlc2021_adapter import DLC2021Adapter
from app.visual_forensics import LocalDeterministicVisualForensics


def evaluate_sidtd_benchmark(
    sidtd_root: str | Path = "data/external/sidtd",
    split: str = "test",
    output_dir: str | Path = "data/evaluations/external/sidtd",
) -> Dict[str, Any]:
    """Run baseline VEDA visual forensics against SIDTD official split."""
    adapter = SIDTDAdapter(resolve_repo_path(str(sidtd_root)))
    out_path = Path(resolve_repo_path(str(output_dir)))
    out_path.mkdir(parents=True, exist_ok=True)

    if not adapter.is_available():
        print(f"[SIDTD] Dataset not ready at {sidtd_root}.")
        return {"status": "UNAVAILABLE", "reason": "Dataset files not extracted."}

    samples = adapter.list_samples(split)
    print(f"\n=======================================================")
    print(f"EVALUATING SIDTD BENCHMARK (Split: {split}, Count: {len(samples)})")
    print(f"=======================================================")

    detector = LocalDeterministicVisualForensics()

    predictions: List[Dict[str, Any]] = []
    y_true: List[int] = []
    y_pred: List[int] = []

    failures: List[Dict[str, Any]] = []

    t0 = time.time()
    for idx, sample in enumerate(samples):
        img_path = Path(sample.source_path)
        if not img_path.is_file():
            # Try alternate path if templates folder structure varies
            alt_path = Path(resolve_repo_path(str(sidtd_root))) / sample.sample_id
            if alt_path.is_file():
                img_path = alt_path
            else:
                continue

        image_bytes = img_path.read_bytes()

        # PREDICTION BOUNDARY: Run detector over raw bytes ONLY
        forensic_res = detector.analyze(image_bytes)

        # Freeze prediction: 1 = Forgery (SUSPICIOUS finding), 0 = Bonafide (PASS)
        is_predicted_forgery = 1 if forensic_res.get("status") == "SUSPICIOUS" else 0
        is_actual_forgery = 1 if sample.ground_truth_class == "FORGERY" else 0

        y_true.append(is_actual_forgery)
        y_pred.append(is_predicted_forgery)

        pred_record = {
            "sample_id": sample.sample_id,
            "document_id": sample.document_id,
            "document_family": sample.document_family,
            "predicted_forgery": is_predicted_forgery,
            "predicted_status": forensic_res.get("status"),
            "findings_count": len(forensic_res.get("findings", [])),
            "findings": [f.get("finding_type") for f in forensic_res.get("findings", [])],
            "ground_truth_class": sample.ground_truth_class,
            "is_actual_forgery": is_actual_forgery,
            "class_name": sample.annotations.get("class_name"),
        }
        predictions.append(pred_record)

        # Record failures
        if is_predicted_forgery != is_actual_forgery:
            failures.append({
                "sample_id": sample.sample_id,
                "error_type": "FALSE_POSITIVE" if is_predicted_forgery == 1 else "FALSE_NEGATIVE",
                "ground_truth": sample.ground_truth_class,
                "prediction": forensic_res.get("status"),
                "findings": forensic_res.get("findings", []),
                "measures": forensic_res.get("measures", {}),
            })

        if (idx + 1) % 50 == 0 or (idx + 1) == len(samples):
            print(f"  Evaluated {idx + 1}/{len(samples)} samples...")

    eval_duration = time.time() - t0
    metrics = calculate_binary_classification_metrics(y_true, y_pred)
    metrics["evaluation_duration_seconds"] = round(eval_duration, 2)
    metrics["throughput_samples_per_sec"] = round(len(y_true) / eval_duration, 2) if eval_duration > 0 else 0

    # Per-template class breakdown
    per_class_results: Dict[str, Dict[str, Any]] = {}
    for p in predictions:
        c_name = p.get("class_name") or "unknown"
        if c_name not in per_class_results:
            per_class_results[c_name] = {"y_true": [], "y_pred": []}
        per_class_results[c_name]["y_true"].append(p["is_actual_forgery"])
        per_class_results[c_name]["y_pred"].append(p["predicted_forgery"])

    per_class_metrics: Dict[str, Any] = {}
    for c_name, data in per_class_results.items():
        per_class_metrics[c_name] = calculate_binary_classification_metrics(data["y_true"], data["y_pred"])

    result_payload = {
        "benchmark_id": "SIDTD",
        "official_source": "TC-11 / Computer Vision Center (CVC)",
        "split": split,
        "split_protocol": "split_normal",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "detector_evaluated": {
            "name": detector.name,
            "version": detector.version,
            "type": "Local Deterministic Heuristics (Pre-Adaptation Baseline)",
        },
        "metrics": metrics,
        "per_class_metrics": per_class_metrics,
        "failure_summary": {
            "false_positives": metrics["false_positives"],
            "false_negatives": metrics["false_negatives"],
            "false_positive_rate": metrics["false_positive_rate"],
            "false_negative_rate": metrics["false_negative_rate"],
        },
        "scientific_boundary": (
            "This evaluates VEDA's initial layout-specific noise/edge heuristics against the external SIDTD dataset. "
            "Because the current heuristic was designed for controlled VEDA synthetic geometry without learned model weights, "
            "these numbers establish the honest uncalibrated baseline (EXTERNAL BASELINE V1) prior to external model training."
        ),
    }

    # Save artifacts
    (out_path / "metrics.json").write_text(json.dumps(result_payload, indent=2))
    (out_path / "prediction_manifest.json").write_text(json.dumps(predictions, indent=2))
    (out_path / "failures.json").write_text(json.dumps(failures, indent=2))
    (out_path / "benchmark_config.json").write_text(
        json.dumps({
            "benchmark_id": "SIDTD",
            "split": split,
            "sample_count": len(samples),
            "source_dir": str(sidtd_root),
        }, indent=2)
    )

    print("\n--- SIDTD EVALUATION METRICS ---")
    print(f"Sample count: {metrics['sample_count']}")
    print(f"Accuracy: {metrics['accuracy'] * 100:.2f}%")
    print(f"Balanced Accuracy: {metrics['balanced_accuracy'] * 100:.2f}%")
    print(f"Precision: {metrics['precision'] * 100:.2f}%")
    print(f"Recall (Sensitivity): {metrics['recall'] * 100:.2f}%")
    print(f"Specificity (TNR): {metrics['specificity'] * 100:.2f}%")
    print(f"F1-Score: {metrics['f1_score']:.4f}")
    print(f"Confusion Matrix: TP={metrics['true_positives']}, FP={metrics['false_positives']}, TN={metrics['true_negatives']}, FN={metrics['false_negatives']}")
    print(f"Saved artifacts to {out_path}")

    return result_payload


def evaluate_fantasyid_benchmark(
    fantasyid_root: str | Path = "data/external/fantasyid",
    split: str = "all",
    output_dir: str | Path = "data/evaluations/external/fantasyid",
) -> Dict[str, Any]:
    """Run baseline VEDA visual forensics against FantasyID dataset."""
    adapter = FantasyIDAdapter(resolve_repo_path(str(fantasyid_root)))
    out_path = Path(resolve_repo_path(str(output_dir)))
    out_path.mkdir(parents=True, exist_ok=True)

    if not adapter.is_available():
        print(f"[FantasyID] Dataset not ready at {fantasyid_root}.")
        return {"status": "UNAVAILABLE", "reason": "FantasyID.tgz not extracted yet."}

    samples = adapter.list_samples(split)
    if not samples:
        return {"status": "UNAVAILABLE", "reason": "No samples found in FantasyID directory."}

    print(f"\n=======================================================")
    print(f"EVALUATING FANTASYID BENCHMARK (Split: {split}, Count: {len(samples)})")
    print(f"=======================================================")

    detector = LocalDeterministicVisualForensics()

    predictions: List[Dict[str, Any]] = []
    y_true: List[int] = []
    y_pred: List[int] = []
    failures: List[Dict[str, Any]] = []

    t0 = time.time()
    for idx, sample in enumerate(samples):
        img_path = Path(sample.source_path)
        if not img_path.is_file():
            continue

        image_bytes = img_path.read_bytes()

        # PREDICTION BOUNDARY: Run detector over raw bytes ONLY
        forensic_res = detector.analyze(image_bytes)

        is_predicted_forgery = 1 if forensic_res.get("status") == "SUSPICIOUS" else 0
        is_actual_forgery = 1 if sample.ground_truth_class == "FORGERY" else 0

        y_true.append(is_actual_forgery)
        y_pred.append(is_predicted_forgery)

        pred_record = {
            "sample_id": sample.sample_id,
            "document_id": sample.document_id,
            "document_family": sample.document_family,
            "predicted_forgery": is_predicted_forgery,
            "predicted_status": forensic_res.get("status"),
            "findings_count": len(forensic_res.get("findings", [])),
            "findings": [f.get("finding_type") for f in forensic_res.get("findings", [])],
            "ground_truth_class": sample.ground_truth_class,
            "is_actual_forgery": is_actual_forgery,
            "language": sample.annotations.get("language"),
        }
        predictions.append(pred_record)

        if is_predicted_forgery != is_actual_forgery:
            failures.append({
                "sample_id": sample.sample_id,
                "error_type": "FALSE_POSITIVE" if is_predicted_forgery == 1 else "FALSE_NEGATIVE",
                "ground_truth": sample.ground_truth_class,
                "prediction": forensic_res.get("status"),
                "findings": forensic_res.get("findings", []),
            })

        if (idx + 1) % 100 == 0 or (idx + 1) == len(samples):
            print(f"  Evaluated {idx + 1}/{len(samples)} samples...")

    eval_duration = time.time() - t0
    metrics = calculate_binary_classification_metrics(y_true, y_pred)
    metrics["evaluation_duration_seconds"] = round(eval_duration, 2)
    metrics["throughput_samples_per_sec"] = round(len(y_true) / eval_duration, 2) if eval_duration > 0 else 0

    # Per-language breakdown
    per_lang_results: Dict[str, Dict[str, Any]] = {}
    for p in predictions:
        lang = p.get("language") or "unknown"
        if lang not in per_lang_results:
            per_lang_results[lang] = {"y_true": [], "y_pred": []}
        per_lang_results[lang]["y_true"].append(p["is_actual_forgery"])
        per_lang_results[lang]["y_pred"].append(p["predicted_forgery"])

    per_lang_metrics: Dict[str, Any] = {}
    for lang, data in per_lang_results.items():
        per_lang_metrics[lang] = calculate_binary_classification_metrics(data["y_true"], data["y_pred"])

    result_payload = {
        "benchmark_id": "FantasyID",
        "official_source": "Idiap Research Institute (Zenodo DOI: 10.34777/c966-nn94)",
        "license": "CC-BY-4.0",
        "split": split,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "detector_evaluated": {
            "name": detector.name,
            "version": detector.version,
            "type": "Local Deterministic Heuristics (Pre-Adaptation Baseline)",
        },
        "metrics": metrics,
        "per_language_metrics": per_lang_metrics,
        "failure_summary": {
            "false_positives": metrics["false_positives"],
            "false_negatives": metrics["false_negatives"],
            "false_positive_rate": metrics["false_positive_rate"],
            "false_negative_rate": metrics["false_negative_rate"],
        },
        "scientific_boundary": (
            "Evaluates baseline heuristic generalizability across 13 distinct international and domestic language templates. "
            "Establishes initial benchmark baseline prior to training learned visual tamper representations."
        ),
    }

    (out_path / "metrics.json").write_text(json.dumps(result_payload, indent=2))
    (out_path / "prediction_manifest.json").write_text(json.dumps(predictions, indent=2))
    (out_path / "failures.json").write_text(json.dumps(failures, indent=2))

    print("\n--- FANTASYID EVALUATION METRICS ---")
    print(f"Sample count: {metrics['sample_count']}")
    print(f"Accuracy: {metrics['accuracy'] * 100:.2f}%")
    print(f"Balanced Accuracy: {metrics['balanced_accuracy'] * 100:.2f}%")
    print(f"Precision: {metrics['precision'] * 100:.2f}%")
    print(f"Recall: {metrics['recall'] * 100:.2f}%")
    print(f"Specificity: {metrics['specificity'] * 100:.2f}%")
    print(f"F1-Score: {metrics['f1_score']:.4f}")
    print(f"Confusion Matrix: TP={metrics['true_positives']}, FP={metrics['false_positives']}, TN={metrics['true_negatives']}, FN={metrics['false_negatives']}")

    return result_payload


def evaluate_dlc2021_benchmark(
    dlc_root: str | Path = "data/external/dlc-2021",
    output_dir: str | Path = "data/evaluations/external/dlc2021",
) -> Dict[str, Any]:
    """Record official DLC-2021 metadata and baseline protocol."""
    adapter = DLC2021Adapter(resolve_repo_path(str(dlc_root)))
    out_path = Path(resolve_repo_path(str(output_dir)))
    out_path.mkdir(parents=True, exist_ok=True)

    if not adapter.is_available():
        return {"status": "UNAVAILABLE", "reason": "DLC-2021 index CSV not found."}

    samples = adapter.list_samples("all")
    print(f"\n=======================================================")
    print(f"EVALUATING DLC-2021 METADATA & BENCHMARK INDEX (Count: {len(samples)})")
    print(f"=======================================================")

    by_type: Dict[str, int] = {}
    by_device: Dict[str, int] = {}
    for s in samples:
        m_type = s.manipulation_type or "unknown"
        by_type[m_type] = by_type.get(m_type, 0) + 1
        dev = s.annotations.get("device") or "unknown"
        by_device[dev] = by_device.get(dev, 0) + 1

    result_payload = {
        "benchmark_id": "DLC-2021",
        "official_source": "Smart Engines / Journal of Imaging (DOI: 10.3390/jimaging8070181)",
        "license": "CC-BY-SA-2.5",
        "total_video_clips": len(samples),
        "modality_breakdown": by_type,
        "device_breakdown": by_device,
        "experimental_baseline_status": "DOWNLOADED (experimental_baseline.zip, 84.3 MB)",
        "full_video_corpus_status": "DEFERRED_DUE_TO_SIZE_POLICY (99 GB total across 4 archives)",
        "scientific_boundary": (
            "DLC-2021 establishes the official presentation attack detection benchmark protocol for mock IDs. "
            "Current VEDA implementation does not yet incorporate video temporal presentation attack analysis; "
            "this baseline explicitly documents that capability boundary without faking coverage."
        ),
    }

    (out_path / "metrics.json").write_text(json.dumps(result_payload, indent=2))
    (out_path / "README.md").write_text(
        "# DLC-2021 Evaluation & Benchmark Protocol\n\n"
        "Official index records 1,424 video sequences across 4 modalities: original mock (356), "
        "grayscale copies (356), color copies (356), and screen recaptures (356).\n"
    )

    print(f"DLC-2021: Total records indexed: {len(samples)}, Modalities: {by_type}")
    return result_payload


def generate_external_summary(results: Dict[str, Any], output_path: str | Path = "data/evaluations/external/external_benchmark_summary.json"):
    out_file = Path(resolve_repo_path(str(output_path)))
    out_file.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "evaluation_scope": "STANDARDIZED EXTERNAL BENCHMARK EVALUATION (BASELINE V1)",
        "benchmarks": results,
    }
    out_file.write_text(json.dumps(summary, indent=2))
    print(f"\nSaved consolidated external benchmark summary to {out_file}")


if __name__ == "__main__":
    sidtd_res = evaluate_sidtd_benchmark()
    fantasyid_res = evaluate_fantasyid_benchmark()
    dlc_res = evaluate_dlc2021_benchmark()
    generate_external_summary({
        "SIDTD": sidtd_res,
        "FantasyID": fantasyid_res,
        "DLC-2021": dlc_res,
    })
