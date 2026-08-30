from __future__ import annotations

from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError


class VisualForensicsAdapter(ABC):
    @abstractmethod
    def analyze(self, image_bytes: bytes) -> dict[str, Any]:
        """Analyze only submitted pixels and return detector measures, never benchmark truth."""


def _robust_z(values: np.ndarray) -> np.ndarray:
    median = np.median(values)
    mad = np.median(np.abs(values - median))
    return np.zeros_like(values) if mad < 1e-9 else 0.6745 * (values - median) / mad


class LocalDeterministicVisualForensics(VisualForensicsAdapter):
    name = "VEDA_LOCAL_IMAGE_FORENSICS"
    version = "1.0"

    def analyze(self, image_bytes: bytes) -> dict[str, Any]:
        try:
            with Image.open(BytesIO(image_bytes)) as opened:
                rgb = np.asarray(opened.convert("RGB"))
                source_format = opened.format
        except (UnidentifiedImageError, OSError, ValueError):
            return self._unavailable("Image pixels could not be decoded.")

        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        if width < 240 or height < 160:
            return self._unavailable("Image is too small for local region analysis.")

        rows, cols = 6, 10
        residual = cv2.absdiff(gray, cv2.GaussianBlur(gray, (0, 0), 1.1)).astype(np.float32)
        noise_measures: list[float] = []
        edge_measures: list[float] = []
        boxes: list[tuple[int, int, int, int]] = []
        for row in range(rows):
            for col in range(cols):
                x1, x2 = col * width // cols, (col + 1) * width // cols
                y1, y2 = row * height // rows, (row + 1) * height // rows
                cell = gray[y1:y2, x1:x2]
                noise_measures.append(float(np.mean(residual[y1:y2, x1:x2])))
                edge_measures.append(float(cv2.Laplacian(cell, cv2.CV_64F).var()))
                boxes.append((x1, y1, x2, y2))
        noise_z = np.abs(_robust_z(np.asarray(noise_measures)))
        edge_z = np.abs(_robust_z(np.log1p(np.asarray(edge_measures))))

        findings: list[dict[str, Any]] = []
        suspicious_indices = np.where((noise_z >= 3.8) & (edge_z >= 2.2))[0].tolist()
        for index in suspicious_indices[:8]:
            x1, y1, x2, y2 = boxes[index]
            findings.append({
                "finding_type": "LOCAL_NOISE_EDGE_INCONSISTENCY",
                "status": "SUSPICIOUS",
                "bounding_box": {"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1},
                "raw_measure": {"noise_robust_z": round(float(noise_z[index]), 3), "edge_robust_z": round(float(edge_z[index]), 3)},
                "explanation": "This region differs strongly from the document's median high-frequency noise and edge profile.",
            })

        # Controlled VEDA fixtures use a documented fictional layout. This is a
        # layout-specific region measure, not a general passport-security claim.
        portrait_anomalies = []
        for index, (x1, y1, x2, y2) in enumerate(boxes):
            center_x, center_y = (x1 + x2) / (2 * width), (y1 + y2) / (2 * height)
            if 0.04 <= center_x <= 0.29 and 0.24 <= center_y <= 0.70 and edge_z[index] >= 2.65:
                portrait_anomalies.append(index)
        for index in portrait_anomalies[:2]:
            x1, y1, x2, y2 = boxes[index]
            findings.append({
                "finding_type": "TEMPLATE_PORTRAIT_REGION_EDGE_ANOMALY",
                "status": "SUSPICIOUS",
                "bounding_box": {"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1},
                "raw_measure": {"edge_robust_z": round(float(edge_z[index]), 3), "configured_threshold": 2.65},
                "explanation": "The documented portrait area of the fictional VEDA fixture has an outlying edge profile relative to the submitted image.",
            })

        copy_move = self._copy_move(gray)
        if copy_move:
            findings.append(copy_move)

        # JPEG recompression is capture-condition evidence, not itself a tamper finding.
        jpeg_measure = None
        if source_format == "JPEG":
            encoded = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])[1]
            recompressed = cv2.imdecode(encoded, cv2.IMREAD_GRAYSCALE)
            jpeg_measure = round(float(np.mean(cv2.absdiff(gray, recompressed))), 3)

        status = "SUSPICIOUS" if findings else "PASS"
        return {
            "status": status,
            "findings": findings,
            "suspicious_regions": [item["bounding_box"] for item in findings if item.get("bounding_box")],
            "detector": {"name": self.name, "version": self.version, "kind": "DETERMINISTIC_HEURISTICS", "probability": None},
            "measures": {
                "grid": [cols, rows],
                "maximum_noise_robust_z": round(float(np.max(noise_z)), 3),
                "maximum_edge_robust_z": round(float(np.max(edge_z)), 3),
                "jpeg_recompression_residual": jpeg_measure,
            },
            "limitations": [
                "A PASS means these local heuristics found no configured anomaly; it does not establish authenticity.",
                "Semantically altered text can be visually clean and may be detectable only through independent evidence such as MRZ consistency.",
            ],
        }

    def _copy_move(self, gray: np.ndarray) -> dict[str, Any] | None:
        orb = cv2.ORB_create(nfeatures=900, fastThreshold=12)
        keypoints, descriptors = orb.detectAndCompute(gray, None)
        if descriptors is None or len(keypoints) < 20:
            return None
        matches = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(descriptors, descriptors, k=3)
        pairs: list[tuple[tuple[float, float], tuple[float, float]]] = []
        displacement_bins: dict[tuple[int, int], list[tuple[tuple[float, float], tuple[float, float]]]] = {}
        diagonal = float(np.hypot(*gray.shape))
        for group in matches:
            for candidate in group[1:]:
                p1, p2 = keypoints[candidate.queryIdx].pt, keypoints[candidate.trainIdx].pt
                if candidate.distance <= 20 and np.hypot(p1[0] - p2[0], p1[1] - p2[1]) > diagonal * 0.12:
                    pairs.append((p1, p2))
                    displacement = (round((p2[0] - p1[0]) / 20), round((p2[1] - p1[1]) / 20))
                    if abs(displacement[1]) >= 3:
                        displacement_bins.setdefault(displacement, []).append((p1, p2))
                    break
        cluster = max(displacement_bins.values(), key=len, default=[])
        if len(cluster) < 12:
            return None
        points = np.asarray([point for pair in cluster for point in pair])
        x1, y1 = np.floor(points.min(axis=0)).astype(int)
        x2, y2 = np.ceil(points.max(axis=0)).astype(int)
        return {
            "finding_type": "DUPLICATE_REGION_INDICATION",
            "status": "SUSPICIOUS",
            "bounding_box": {"x": int(x1), "y": int(y1), "width": int(x2 - x1), "height": int(y2 - y1)},
            "raw_measure": {"consistent_displacement_feature_pairs": len(cluster), "all_candidate_pairs": len(pairs)},
            "explanation": "Multiple spatially separated local features have unusually similar descriptors; repetitive design elements can also cause this finding.",
        }

    def _unavailable(self, reason: str) -> dict[str, Any]:
        return {"status": "UNAVAILABLE", "findings": [], "suspicious_regions": [], "detector": {"name": self.name, "version": self.version, "kind": "DETERMINISTIC_HEURISTICS", "probability": None}, "measures": {}, "limitations": [reason]}
