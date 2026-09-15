from __future__ import annotations

from io import BytesIO
from typing import Any

import numpy as np
import cv2
from PIL import Image, ImageOps


def preprocess_specimen(data: bytes) -> tuple[bytes, dict[str, Any]]:
    """Apply small deterministic corrections while retaining the original bytes."""
    with Image.open(BytesIO(data)) as opened:
        original = opened.size
        image = ImageOps.exif_transpose(opened).convert("RGB")
        operations: list[str] = []
        if image.size != original:
            operations.append("EXIF_ORIENTATION")
        arr = np.asarray(image)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        # Conservative scanner-margin trim: only accept a large rectangular
        # foreground region with a clear border; otherwise keep the full image.
        _, mask = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h, w = gray.shape
        best = None
        candidates = []
        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour); area = cw * ch / float(w * h)
            touches_edge = x <= 2 or y <= 2 or x + cw >= w - 2 or y + ch >= h - 2
            if area >= 0.06 and not touches_edge and cw / max(ch, 1) > 0.35 and ch / max(cw, 1) > 0.35:
                candidates.append((area, x, y, cw, ch))
        if candidates:
            area, x, y, cw, ch = max(candidates)
            best = (x, y, cw, ch, area)
        localization = {"document_region_detected": bool(best), "document_quad": None, "localization_score": round(best[4], 4) if best else 0.0, "localization_method": "foreground_contour" if best else "full_image_fallback", "perspective_rectified": False}
        if best and best[4] < 0.95:
            x, y, cw, ch, _ = best
            image = image.crop((x, y, x + cw, y + ch))
            operations.append("DOCUMENT_REGION_CROP")
        mean = float(np.asarray(image.convert("L")).mean())
        if mean > 225 or mean < 30:
            image = ImageOps.autocontrast(image, cutoff=1)
            operations.append("AUTOCONTRAST")
        output = BytesIO()
        image.save(output, format="PNG")
        processed = output.getvalue()
    return processed, {"original_dimensions": {"width": original[0], "height": original[1]}, "processed_dimensions": {"width": image.width, "height": image.height}, "operations": operations, **localization, "selected_rotation": 0, "orientation_reason": "EXIF-corrected baseline; no safe rotation confidence improvement was established."}
