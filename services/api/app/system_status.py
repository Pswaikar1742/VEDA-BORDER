from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import cv2

from app.config import resolve_repo_path, settings


def module_status() -> dict[str, Any]:
    tesseract_ready = shutil.which("tesseract") is not None
    detector_file = Path(resolve_repo_path(settings.face_detector_model))
    recognizer_file = Path(resolve_repo_path(settings.face_recognizer_model))
    models_ready = detector_file.is_file() and recognizer_file.is_file() and hasattr(cv2, "FaceRecognizerSF")
    db_path = Path(resolve_repo_path(settings.case_database_path))
    database_parent_ready = db_path.parent.exists() or db_path.parent.parent.exists()
    modules = [
        {"module": "OCR", "state": "READY" if tesseract_ready else "UNAVAILABLE", "detail": "Local Tesseract executable detected." if tesseract_ready else "Tesseract executable not found."},
        {"module": "MRZ", "state": "READY" if tesseract_ready else "UNAVAILABLE", "detail": "Pixel OCR plus deterministic TD3-style parser."},
        {"module": "Rules", "state": "READY", "detail": "Deterministic family-aware rules."},
        {"module": "Consistency", "state": "READY", "detail": "Deterministic semantic VIZ-to-MRZ comparison."},
        {"module": "Visual Forensics", "state": "READY" if settings.visual_forensics_enabled else "UNAVAILABLE", "detail": "Local deterministic image heuristics; no learned tamper model."},
        {"module": "Face Verification", "state": "READY" if settings.biometrics_enabled and models_ready else "UNAVAILABLE", "detail": "Local OpenCV YuNet and SFace model assets."},
        {"module": "Threat Intelligence", "state": "READY" if settings.mock_border_intelligence_enabled else "UNAVAILABLE", "detail": "LOCAL PROTOTYPE WATCHLIST; no external government lookup."},
        {"module": "Identity Linkage", "state": "READY" if database_parent_ready else "DEGRADED", "detail": "Local SQLite embedding linkage store."},
        {"module": "Evidence Graph", "state": "READY", "detail": "Policy-tiered evidence provenance graph."},
        {"module": "Coverage Governor", "state": "READY", "detail": "Mandatory evidence and hard-gate policy engine."},
        {"module": "FastRouter", "state": "READY" if settings.fast_router_enabled and settings.fast_router_api_key else "UNAVAILABLE", "detail": "Optional provider is enabled." if settings.fast_router_enabled and settings.fast_router_api_key else "Optional provider disabled; core workflow remains local."},
    ]
    core = [item for item in modules if item["module"] != "FastRouter"]
    overall = "READY" if all(item["state"] == "READY" for item in core) else ("UNAVAILABLE" if any(item["state"] == "UNAVAILABLE" for item in core) else "DEGRADED")
    return {"status": overall, "research_prototype": True, "modules": modules}
