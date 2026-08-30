from __future__ import annotations

from io import BytesIO
from typing import Any

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError


def _finding(check: str, state: str, measure: float | list[int] | None, threshold: str, explanation: str) -> dict[str, Any]:
    return {"check": check, "state": state, "measure": measure, "threshold": threshold, "explanation": explanation}


def assess_capture_quality(image_bytes: bytes, min_width: int = 700, min_height: int = 440) -> dict[str, Any]:
    try:
        with Image.open(BytesIO(image_bytes)) as opened:
            rgb = np.asarray(opened.convert("RGB"))
    except (UnidentifiedImageError, OSError, ValueError):
        return {"status": "FAILED_TO_EXECUTE", "acceptable": False, "findings": [_finding("decode", "FAIL", None, "valid PNG/JPEG pixels", "Image pixels could not be decoded.")], "recommendation": "RECAPTURE_DOCUMENT"}

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    height, width = gray.shape
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(np.mean(gray))
    dark_fraction = float(np.mean(gray < 20))
    bright_fraction = float(np.mean(gray > 245))
    edge_pixels = cv2.Canny(gray, 60, 160)
    edge_density = float(np.mean(edge_pixels > 0))

    findings = [
        _finding("resolution", "PASS" if width >= min_width and height >= min_height else "FAIL", [width, height], f">={min_width}x{min_height}", "Image resolution is adequate." if width >= min_width and height >= min_height else "Image resolution is below the prototype extraction minimum."),
        _finding("blur", "PASS" if blur >= 45.0 else "FAIL", round(blur, 2), "variance_of_laplacian>=45", "Local sharpness is adequate." if blur >= 45.0 else "Image appears excessively blurred."),
        _finding("brightness", "PASS" if 45.0 <= brightness <= 220.0 else "FAIL", round(brightness, 2), "45<=mean_gray<=220", "Mean brightness is usable." if 45.0 <= brightness <= 220.0 else "Image is extremely dark or bright."),
        _finding("exposure_clipping", "PASS" if dark_fraction < 0.40 and bright_fraction < 0.55 else "FAIL", round(max(dark_fraction, bright_fraction), 4), "dark<0.40 and bright<0.55", "Exposure retains usable tonal information." if dark_fraction < 0.40 and bright_fraction < 0.55 else "A large fraction of pixels is clipped."),
        _finding("document_crop", "PASS" if edge_density >= 0.008 else "SUSPICIOUS", round(edge_density, 4), "edge_density>=0.008", "Document-like edge and text content is present." if edge_density >= 0.008 else "Document crop/content could not be established confidently."),
    ]
    failed = [item for item in findings if item["state"] == "FAIL"]
    return {
        "status": "FAIL" if failed else ("SUSPICIOUS" if any(item["state"] == "SUSPICIOUS" for item in findings) else "PASS"),
        "acceptable": not failed,
        "findings": findings,
        "recommendation": "RECAPTURE_DOCUMENT" if failed else None,
        "detector": {"name": "VEDA_LOCAL_CAPTURE_QUALITY", "version": "1.0", "probability": None},
    }
