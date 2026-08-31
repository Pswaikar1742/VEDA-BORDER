from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CURRENT_FILE = Path(__file__).resolve()
API_ROOT = CURRENT_FILE.parent.parent
REPO_ROOT = API_ROOT.parent.parent

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import resolve_repo_path, settings
from app.document_families import classify_document
from app.extraction import extract_specimen
from app.mrz import parse_mrz
from app.quality import assess_capture_quality
from app.external_benchmarks.midv2020_adapter import MIDV2020Adapter


def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def compute_cer(pred: str, target: str) -> float:
    if not target:
        return 0.0 if not pred else 1.0
    dist = levenshtein_distance(pred, target)
    return dist / len(target)


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.upper()
    text = re.sub(r"[^A-Z0-9 ]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_photo_condition(sample_idx: int) -> Tuple[str, str]:
    if 0 <= sample_idx <= 9:
        return "projective_distortions", "iphone_xr"
    elif 20 <= sample_idx <= 24:
        return "text_documents_background", "iphone_xr"
    elif 30 <= sample_idx <= 34:
        return "keyboard_background", "iphone_xr"
    elif 40 <= sample_idx <= 44:
        return "natural_lighting_outdoors", "iphone_xr"
    elif 50 <= sample_idx <= 54:
        return "table_background", "iphone_xr"
    elif 60 <= sample_idx <= 64:
        return "highlight_glare_present", "iphone_xr"
    elif 70 <= sample_idx <= 79:
        return "low_lighting", "iphone_xr"
    elif 90 <= sample_idx <= 94:
        return "cloth_background", "iphone_xr"
    elif 10 <= sample_idx <= 19:
        return "projective_distortions", "samsung_s10"
    elif 25 <= sample_idx <= 29:
        return "text_documents_background", "samsung_s10"
    elif 35 <= sample_idx <= 39:
        return "keyboard_background", "samsung_s10"
    elif 45 <= sample_idx <= 49:
        return "natural_lighting_outdoors", "samsung_s10"
    elif 55 <= sample_idx <= 59:
        return "table_background", "samsung_s10"
    elif 65 <= sample_idx <= 69:
        return "highlight_glare_present", "samsung_s10"
    elif 80 <= sample_idx <= 89:
        return "low_lighting", "samsung_s10"
    elif 95 <= sample_idx <= 99:
        return "cloth_background", "samsung_s10"
    return "standard_capture", "unknown"


def evaluate_single_sample(sample_meta: Dict[str, Any]) -> Dict[str, Any]:
    source_path = Path(sample_meta["source_path"])
    image_bytes = source_path.read_bytes()

    t0 = time.time()
    quality = assess_capture_quality(image_bytes, settings.minimum_image_width, settings.minimum_image_height)
    extraction = extract_specimen(image_bytes)
    classification = classify_document(extraction["raw_ocr_text"])
    mrz = parse_mrz(extraction["raw_mrz_text"])
    duration = time.time() - t0

    frozen_prediction = {
        "sample_id": sample_meta["sample_id"],
        "document_id": sample_meta["document_id"],
        "modality": sample_meta["modality"],
        "document_type": sample_meta["document_type"],
        "document_family": sample_meta["document_family"],
        "sample_index": sample_meta["sample_index"],
        "duration_seconds": round(duration, 3),
        "quality_acceptable": quality["acceptable"],
        "quality_findings": [f["check"] for f in quality.get("findings", []) if f.get("state") == "FAIL"],
        "predicted_family": classification["family"],
        "raw_visible_fields": extraction["raw_visible_fields"],
        "visible_fields": extraction["visible_fields"],
        "field_confidence": extraction["field_confidence"],
        "raw_visible_text": extraction["raw_visible_text"],
        "raw_mrz_text": extraction["raw_mrz_text"],
        "raw_ocr_text": extraction["raw_ocr_text"],
        "mrz_detected": mrz.detected,
        "mrz_fields": mrz.fields,
        "mrz_checks": mrz.checks,
        "mrz_error": mrz.error,
    }

    gt_fields = sample_meta.get("gt_fields", {})
    field_evals: Dict[str, Any] = {}

    exact_matches = 0
    normalized_matches = 0
    substring_matches = 0
    total_evaluable_fields = 0
    total_cer_sum = 0.0

    raw_ocr_normalized = normalize_text(extraction["raw_ocr_text"])

    for field_name, field_data in gt_fields.items():
        gt_val = field_data.get("value", "").strip()
        if not gt_val:
            continue

        total_evaluable_fields += 1
        gt_norm = normalize_text(gt_val)

        pred_val = extraction["visible_fields"].get(field_name) or extraction["raw_visible_fields"].get(field_name) or ""
        pred_norm = normalize_text(pred_val)

        is_exact = (pred_val.strip() == gt_val)
        is_normalized = (pred_norm == gt_norm) and bool(gt_norm)
        is_substring = (gt_norm in raw_ocr_normalized) and bool(gt_norm)

        field_cer = compute_cer(pred_norm, gt_norm)
        total_cer_sum += field_cer

        if is_exact:
            exact_matches += 1
        if is_normalized:
            normalized_matches += 1
        if is_substring:
            substring_matches += 1

        field_evals[field_name] = {
            "gt_value": gt_val,
            "pred_value": pred_val,
            "exact_match": is_exact,
            "normalized_match": is_normalized,
            "substring_match": is_substring,
            "cer": round(field_cer, 3),
            "failed_extraction": not bool(pred_val),
        }

    doc_all_exact = (exact_matches == total_evaluable_fields) if total_evaluable_fields > 0 else False
    doc_all_normalized = (normalized_matches == total_evaluable_fields) if total_evaluable_fields > 0 else False
    doc_any_error = (exact_matches < total_evaluable_fields) if total_evaluable_fields > 0 else False
    doc_total_failure = (exact_matches == 0 and substring_matches == 0) if total_evaluable_fields > 0 else True
    mean_cer = (total_cer_sum / total_evaluable_fields) if total_evaluable_fields > 0 else 0.0

    try:
        s_idx = int(sample_meta["sample_index"])
    except ValueError:
        s_idx = 0
    condition, device = get_photo_condition(s_idx) if sample_meta["modality"] == "photo" else ("standard_scan", "flatbed")

    mrz_applicable = sample_meta["document_type"] in {"aze_passport", "grc_passport", "lva_passport", "srb_passport"}
    mrz_valid = False
    if mrz_applicable and mrz.detected:
        mrz_valid = all(v == "PASS" for v in mrz.checks.values()) if mrz.checks else False

    result_record = {
        **frozen_prediction,
        "evaluable_fields_count": total_evaluable_fields,
        "exact_matches_count": exact_matches,
        "normalized_matches_count": normalized_matches,
        "substring_matches_count": substring_matches,
        "doc_all_exact": doc_all_exact,
        "doc_all_normalized": doc_all_normalized,
        "doc_any_error": doc_any_error,
        "doc_total_failure": doc_total_failure,
        "mean_cer": round(mean_cer, 4),
        "photo_condition": condition,
        "photo_device": device,
        "mrz_applicable": mrz_applicable,
        "mrz_all_checks_passed": mrz_valid,
        "field_evaluations": field_evals,
    }

    return result_record


def evaluate_midv2020_baseline(
    midv_root: str | Path = "data/external/midv-2020",
    output_dir: str | Path = "data/evaluations/external/midv2020/baseline_v1",
    max_workers: int = 16,
) -> Dict[str, Any]:
    out_path = Path(resolve_repo_path(str(output_dir)))
    out_path.mkdir(parents=True, exist_ok=True)

    adapter = MIDV2020Adapter(resolve_repo_path(str(midv_root)))
    if not adapter.is_available():
        print(f"[MIDV-2020] Dataset not ready at {midv_root}.")
        return {"status": "UNAVAILABLE", "reason": "MIDV-2020 images not extracted."}

    all_samples = adapter.list_samples("all")
    print()
    print("=" * 55)
    print(f"EVALUATING MIDV-2020 EXTERNAL OCR BASELINE V1 ({len(all_samples)} samples)")
    print(f"Workers: {max_workers} threads across 4 modalities")
    print("=" * 55)
    print()

    sample_meta_list = []
    for s in all_samples:
        sample_meta_list.append({
            "sample_id": s.sample_id,
            "document_id": s.document_id,
            "source_path": s.source_path,
            "modality": s.annotations.get("modality", s.split),
            "document_type": s.annotations.get("document_type", "unknown"),
            "document_family": s.document_family,
            "sample_index": s.annotations.get("sample_index", "00"),
            "gt_fields": s.annotations.get("fields", {}),
        })

    t_start = time.time()
    results: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(evaluate_single_sample, sm): sm for sm in sample_meta_list}
        completed = 0
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            completed += 1
            if completed % 200 == 0 or completed == len(all_samples):
                pct = (completed / len(all_samples)) * 100
                elapsed = time.time() - t_start
                rate = completed / elapsed if elapsed > 0 else 0
                print(f"  Processed {completed:4d}/{len(all_samples)} samples ({pct:5.1f}%) @ {rate:.2f} samples/sec...")

    total_duration = time.time() - t_start
    print(f"Completed inference over {len(results)} samples in {total_duration:.1f}s ({len(results)/total_duration:.2f} samples/sec).")

    results.sort(key=lambda r: (r["modality"], r["document_type"], r["sample_index"]))

    modality_metrics: Dict[str, Any] = {}
    doctype_metrics: Dict[str, Any] = {}
    field_metrics: Dict[str, Any] = {}
    device_metrics: Dict[str, Any] = {}

    modalities = ["templates", "scan_upright", "scan_rotated", "photo"]
    for mod in modalities:
        mod_res = [r for r in results if r["modality"] == mod]
        if not mod_res:
            continue

        tot_fields = sum(r["evaluable_fields_count"] for r in mod_res)
        exact_matches = sum(r["exact_matches_count"] for r in mod_res)
        norm_matches = sum(r["normalized_matches_count"] for r in mod_res)
        sub_matches = sum(r["substring_matches_count"] for r in mod_res)
        total_cer = sum(r["mean_cer"] * r["evaluable_fields_count"] for r in mod_res)

        all_exact_docs = sum(1 for r in mod_res if r["doc_all_exact"])
        all_norm_docs = sum(1 for r in mod_res if r["doc_all_normalized"])
        any_err_docs = sum(1 for r in mod_res if r["doc_any_error"])
        failed_docs = sum(1 for r in mod_res if r["doc_total_failure"])
        qual_pass = sum(1 for r in mod_res if r["quality_acceptable"])

        modality_metrics[mod] = {
            "sample_count": len(mod_res),
            "total_annotated_fields": tot_fields,
            "exact_field_match_rate": round(exact_matches / tot_fields, 4) if tot_fields > 0 else 0.0,
            "normalized_field_match_rate": round(norm_matches / tot_fields, 4) if tot_fields > 0 else 0.0,
            "substring_ocr_match_rate": round(sub_matches / tot_fields, 4) if tot_fields > 0 else 0.0,
            "character_error_rate": round(total_cer / tot_fields, 4) if tot_fields > 0 else 0.0,
            "field_extraction_failure_rate": round((tot_fields - norm_matches) / tot_fields, 4) if tot_fields > 0 else 0.0,
            "document_all_fields_exact_rate": round(all_exact_docs / len(mod_res), 4),
            "document_all_fields_normalized_rate": round(all_norm_docs / len(mod_res), 4),
            "document_with_field_errors_rate": round(any_err_docs / len(mod_res), 4),
            "document_total_extraction_failure_rate": round(failed_docs / len(mod_res), 4),
            "capture_quality_pass_rate": round(qual_pass / len(mod_res), 4),
        }

    doctypes = sorted(list(set(r["document_type"] for r in results)))
    for dt in doctypes:
        dt_res = [r for r in results if r["document_type"] == dt]
        tot_fields = sum(r["evaluable_fields_count"] for r in dt_res)
        exact_matches = sum(r["exact_matches_count"] for r in dt_res)
        norm_matches = sum(r["normalized_matches_count"] for r in dt_res)
        sub_matches = sum(r["substring_matches_count"] for r in dt_res)
        total_cer = sum(r["mean_cer"] * r["evaluable_fields_count"] for r in dt_res)

        doctype_metrics[dt] = {
            "sample_count": len(dt_res),
            "document_family": dt_res[0]["document_family"],
            "total_annotated_fields": tot_fields,
            "exact_field_match_rate": round(exact_matches / tot_fields, 4) if tot_fields > 0 else 0.0,
            "normalized_field_match_rate": round(norm_matches / tot_fields, 4) if tot_fields > 0 else 0.0,
            "substring_ocr_match_rate": round(sub_matches / tot_fields, 4) if tot_fields > 0 else 0.0,
            "character_error_rate": round(total_cer / tot_fields, 4) if tot_fields > 0 else 0.0,
            "capture_quality_pass_rate": round(sum(1 for r in dt_res if r["quality_acceptable"]) / len(dt_res), 4),
        }

    field_counts: Dict[str, Dict[str, int]] = {}
    field_cer_sum: Dict[str, float] = {}
    for r in results:
        for fname, feval in r.get("field_evaluations", {}).items():
            if fname not in field_counts:
                field_counts[fname] = {"total": 0, "exact": 0, "norm": 0, "sub": 0, "failed": 0}
                field_cer_sum[fname] = 0.0
            field_counts[fname]["total"] += 1
            if feval["exact_match"]:
                field_counts[fname]["exact"] += 1
            if feval["normalized_match"]:
                field_counts[fname]["norm"] += 1
            if feval["substring_match"]:
                field_counts[fname]["sub"] += 1
            if feval["failed_extraction"]:
                field_counts[fname]["failed"] += 1
            field_cer_sum[fname] += feval["cer"]

    for fname, fc in sorted(field_counts.items()):
        tot = fc["total"]
        field_metrics[fname] = {
            "total_samples": tot,
            "exact_match_rate": round(fc["exact"] / tot, 4) if tot > 0 else 0.0,
            "normalized_match_rate": round(fc["norm"] / tot, 4) if tot > 0 else 0.0,
            "substring_match_rate": round(fc["sub"] / tot, 4) if tot > 0 else 0.0,
            "extraction_failure_rate": round(fc["failed"] / tot, 4) if tot > 0 else 0.0,
            "character_error_rate": round(field_cer_sum[fname] / tot, 4) if tot > 0 else 0.0,
        }

    mrz_res = [r for r in results if r["mrz_applicable"]]
    mrz_detected = sum(1 for r in mrz_res if r["mrz_detected"])
    mrz_all_pass = sum(1 for r in mrz_res if r["mrz_all_checks_passed"])
    mrz_metrics = {
        "mrz_applicable_samples": len(mrz_res),
        "mrz_detected_count": mrz_detected,
        "mrz_detection_rate": round(mrz_detected / len(mrz_res), 4) if mrz_res else 0.0,
        "mrz_all_checks_pass_count": mrz_all_pass,
        "mrz_all_checks_pass_rate": round(mrz_all_pass / len(mrz_res), 4) if mrz_res else 0.0,
        "per_modality_mrz_detection": {
            mod: round(sum(1 for r in mrz_res if r["modality"] == mod and r["mrz_detected"]) / sum(1 for r in mrz_res if r["modality"] == mod), 4)
            for mod in modalities
        },
    }

    photo_res = [r for r in results if r["modality"] == "photo"]
    for dev in ["samsung_s10", "iphone_xr"]:
        dev_samples = [r for r in photo_res if r["photo_device"] == dev]
        tot_f = sum(r["evaluable_fields_count"] for r in dev_samples)
        norm_m = sum(r["normalized_matches_count"] for r in dev_samples)
        sub_m = sum(r["substring_matches_count"] for r in dev_samples)
        cer_sum = sum(r["mean_cer"] * r["evaluable_fields_count"] for r in dev_samples)
        qual_p = sum(1 for r in dev_samples if r["quality_acceptable"])

        device_metrics[dev] = {
            "sample_count": len(dev_samples),
            "exact_field_match_rate": round(sum(r["exact_matches_count"] for r in dev_samples) / tot_f, 4) if tot_f > 0 else 0.0,
            "normalized_field_match_rate": round(norm_m / tot_f, 4) if tot_f > 0 else 0.0,
            "substring_ocr_match_rate": round(sub_m / tot_f, 4) if tot_f > 0 else 0.0,
            "character_error_rate": round(cer_sum / tot_f, 4) if tot_f > 0 else 0.0,
            "capture_quality_pass_rate": round(qual_p / len(dev_samples), 4) if dev_samples else 0.0,
        }

    quality_findings_counts: Dict[str, int] = {}
    for r in results:
        for f in r.get("quality_findings", []):
            quality_findings_counts[f] = quality_findings_counts.get(f, 0) + 1

    quality_metrics = {
        "total_samples": len(results),
        "overall_quality_pass_count": sum(1 for r in results if r["quality_acceptable"]),
        "overall_quality_pass_rate": round(sum(1 for r in results if r["quality_acceptable"]) / len(results), 4),
        "per_modality_pass_rate": {mod: modality_metrics[mod]["capture_quality_pass_rate"] for mod in modalities if mod in modality_metrics},
        "quality_gate_failure_reasons": quality_findings_counts,
    }

    failures: List[Dict[str, Any]] = []
    for r in results:
        if r["doc_any_error"] or not r["quality_acceptable"]:
            failures.append({
                "sample_id": r["sample_id"],
                "modality": r["modality"],
                "document_type": r["document_type"],
                "photo_condition": r["photo_condition"],
                "photo_device": r["photo_device"],
                "quality_acceptable": r["quality_acceptable"],
                "quality_findings": r["quality_findings"],
                "mrz_detected": r["mrz_detected"],
                "exact_matches": str(r['exact_matches_count']) + '/' + str(r['evaluable_fields_count']),
                "mean_cer": r["mean_cer"],
                "raw_ocr_preview": r["raw_ocr_text"][:200],
            })

    all_tot_fields = sum(r["evaluable_fields_count"] for r in results)
    all_exact = sum(r["exact_matches_count"] for r in results)
    all_norm = sum(r["normalized_matches_count"] for r in results)
    all_sub = sum(r["substring_matches_count"] for r in results)
    all_cer = sum(r["mean_cer"] * r["evaluable_fields_count"] for r in results)

    overall_metrics = {
        "benchmark_id": "MIDV-2020",
        "benchmark_name": "MIDV-2020 External OCR & Field Extraction Baseline V1",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "total_samples": len(results),
        "total_unique_documents": len(set(r["document_id"] for r in results)),
        "total_annotated_fields": all_tot_fields,
        "field_exact_match_rate": round(all_exact / all_tot_fields, 4) if all_tot_fields > 0 else 0.0,
        "field_normalized_match_rate": round(all_norm / all_tot_fields, 4) if all_tot_fields > 0 else 0.0,
        "field_substring_ocr_match_rate": round(all_sub / all_tot_fields, 4) if all_tot_fields > 0 else 0.0,
        "character_error_rate": round(all_cer / all_tot_fields, 4) if all_tot_fields > 0 else 0.0,
        "field_extraction_failure_rate": round((all_tot_fields - all_norm) / all_tot_fields, 4) if all_tot_fields > 0 else 0.0,
        "document_all_fields_exact_rate": round(sum(1 for r in results if r["doc_all_exact"]) / len(results), 4),
        "document_all_fields_normalized_rate": round(sum(1 for r in results if r["doc_all_normalized"]) / len(results), 4),
        "document_with_field_errors_rate": round(sum(1 for r in results if r["doc_any_error"]) / len(results), 4),
        "document_total_extraction_failure_rate": round(sum(1 for r in results if r["doc_total_failure"]) / len(results), 4),
        "localization_status": "LOCALIZATION METRIC NOT CURRENTLY SUPPORTED (V1 uses static template crop heuristics rather than dynamic bounding-box regression)",
        "throughput_samples_per_sec": round(len(results) / total_duration, 2),
        "total_evaluation_duration_seconds": round(total_duration, 2),
    }

    metrics_payload = {
        "overall": overall_metrics,
        "per_modality": modality_metrics,
        "per_document_type": doctype_metrics,
        "per_field": field_metrics,
        "quality_gate": quality_metrics,
        "mrz_evaluation": mrz_metrics,
        "device_breakdown": device_metrics,
    }
    (out_path / "metrics.json").write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    config_payload = {
        "benchmark_id": "MIDV-2020",
        "version": "BASELINE_V1",
        "dataset_root": str(midv_root),
        "total_samples": len(results),
        "modalities": modalities,
        "workers": max_workers,
        "ocr_engine": "Tesseract 5 local",
        "tesseract_psm": 6,
        "tesseract_lang": "eng",
        "capture_quality_thresholds": {
            "min_width": settings.minimum_image_width,
            "min_height": settings.minimum_image_height,
        },
    }
    (out_path / "benchmark_config.json").write_text(json.dumps(config_payload, indent=2), encoding="utf-8")

    (out_path / "mrz_metrics.json").write_text(json.dumps(mrz_metrics, indent=2), encoding="utf-8")
    (out_path / "quality_gate_metrics.json").write_text(json.dumps(quality_metrics, indent=2), encoding="utf-8")
    (out_path / "failures.json").write_text(json.dumps(failures[:500], indent=2), encoding="utf-8")

    prediction_manifest = [
        {k: v for k, v in r.items() if k != "field_evaluations"}
        for r in results
    ]
    (out_path / "prediction_manifest.json").write_text(json.dumps(prediction_manifest, indent=2), encoding="utf-8")

    with open(out_path / "per_modality.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["modality", "samples", "exact_match_rate", "norm_match_rate", "substring_match_rate", "cer", "field_failure_rate", "doc_all_exact_rate", "quality_pass_rate"])
        for mod, m in modality_metrics.items():
            writer.writerow([mod, m["sample_count"], m["exact_field_match_rate"], m["normalized_field_match_rate"], m["substring_ocr_match_rate"], m["character_error_rate"], m["field_extraction_failure_rate"], m["document_all_fields_exact_rate"], m["capture_quality_pass_rate"]])

    with open(out_path / "per_document_type.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["document_type", "family", "samples", "exact_match_rate", "norm_match_rate", "substring_match_rate", "cer", "quality_pass_rate"])
        for dt, m in doctype_metrics.items():
            writer.writerow([dt, m["document_family"], m["sample_count"], m["exact_field_match_rate"], m["normalized_field_match_rate"], m["substring_ocr_match_rate"], m["character_error_rate"], m["capture_quality_pass_rate"]])

    with open(out_path / "per_field_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["field_name", "total_samples", "exact_match_rate", "normalized_match_rate", "substring_match_rate", "extraction_failure_rate", "character_error_rate"])
        for fn, m in field_metrics.items():
            writer.writerow([fn, m["total_samples"], m["exact_match_rate"], m["normalized_match_rate"], m["substring_match_rate"], m["extraction_failure_rate"], m["character_error_rate"]])

    with open(out_path / "per_sample_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_id", "modality", "document_type", "document_family", "sample_index", "quality_acceptable", "mrz_detected", "exact_matches", "total_fields", "mean_cer", "photo_condition", "photo_device"])
        for r in results:
            writer.writerow([r["sample_id"], r["modality"], r["document_type"], r["document_family"], r["sample_index"], r["quality_acceptable"], r["mrz_detected"], r["exact_matches_count"], r["evaluable_fields_count"], r["mean_cer"], r["photo_condition"], r["photo_device"]])

    exact_pct = overall_metrics["field_exact_match_rate"] * 100
    norm_pct = overall_metrics["field_normalized_match_rate"] * 100
    sub_pct = overall_metrics["field_substring_ocr_match_rate"] * 100
    cer_pct = overall_metrics["character_error_rate"] * 100
    qual_pct = quality_metrics["overall_quality_pass_rate"] * 100
    mrz_pct = mrz_metrics["mrz_detection_rate"] * 100

    baseline_readme = f"""# MIDV-2020 External OCR Baseline V1

- **Evaluated At:** {overall_metrics['evaluated_at']}
- **Total Samples Evaluated:** {overall_metrics['total_samples']} across 4 modalities (1,000 unique document identities)
- **Field Exact Match Rate:** {exact_pct:.2f}%
- **Field Normalized Match Rate:** {norm_pct:.2f}%
- **Substring OCR Match Rate:** {sub_pct:.2f}%
- **Mean Character Error Rate (CER):** {cer_pct:.2f}%
- **Capture Quality Pass Rate:** {qual_pct:.2f}%
- **MRZ Detection Rate (Passports):** {mrz_pct:.2f}%

## Scientific Invariants
This frozen baseline evaluates VEDA-BORDER un-tuned V1 OCR, MRZ, and quality-gate heuristics over raw pixel inputs.
Predictions were frozen before comparing against ground-truth VIA annotations.
"""
    (out_path / "README.md").write_text(baseline_readme, encoding="utf-8")

    freeze_payload = {
        "baseline_identifier": "MIDV2020_EXTERNAL_OCR_BASELINE_V1",
        "freeze_timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": "ec671dc0369b5c41a13a40448a6d22d30ce886b8",
        "dataset_manifest_hash": hashlib.sha256((Path(midv_root) / "DATASET_MANIFEST.json").read_bytes()).hexdigest(),
        "checksums_hash": hashlib.sha256((Path(midv_root) / "CHECKSUMS.json").read_bytes()).hexdigest(),
        "python_version": platform.python_version(),
        "operating_system": platform.platform(),
        "tesseract_version": "5.5.0",
        "ocr_psm": 6,
        "ocr_lang": "eng",
        "ocr_whitelist_mrz": "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<",
        "quality_gate_thresholds": {
            "min_width": settings.minimum_image_width,
            "min_height": settings.minimum_image_height,
        },
        "overall_metrics": overall_metrics,
        "per_modality_metrics": modality_metrics,
        "per_document_type_metrics": doctype_metrics,
        "quality_gate_metrics": quality_metrics,
        "mrz_metrics": mrz_metrics,
        "device_metrics": device_metrics,
    }
    (out_path / "MIDV2020_BASELINE_V1_FREEZE.json").write_text(json.dumps(freeze_payload, indent=2), encoding="utf-8")

    print("\n--- MIDV-2020 EXTERNAL OCR BASELINE V1 RESULTS ---")
    print(f"Total Samples: {overall_metrics['total_samples']}")
    print(f"Field Exact Match: {exact_pct:.2f}%")
    print(f"Field Normalized Match: {norm_pct:.2f}%")
    print(f"Substring OCR Match (Text in OCR): {sub_pct:.2f}%")
    print(f"Character Error Rate (CER): {cer_pct:.2f}%")
    print(f"Extraction Failure Rate: {overall_metrics['field_extraction_failure_rate'] * 100:.2f}%")
    print(f"Capture Quality Pass Rate: {qual_pct:.2f}%")
    print(f"MRZ Detection Rate (Passports): {mrz_pct:.2f}%")
    print(f"Saved all baseline artifacts to {out_path}")

    return metrics_payload


if __name__ == "__main__":
    evaluate_midv2020_baseline()
