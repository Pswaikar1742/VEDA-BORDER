from __future__ import annotations

from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError


from app.config import resolve_repo_path


class FaceVerificationAdapter(ABC):
    @abstractmethod
    def verify(self, document_image: bytes, live_image: bytes | None, portrait_region: tuple[float, float, float, float]) -> dict[str, Any]:
        """Return a local 1:1 comparison and an internal embedding when available."""


class OpenCvSFaceAdapter(FaceVerificationAdapter):
    model_name = "OpenCV YuNet + SFace"
    model_version = "YuNet-2023mar / SFace-2021dec"

    def __init__(self, detector_path: str, recognizer_path: str, threshold: float = 0.55, enabled: bool = True) -> None:
        self.detector_path = Path(resolve_repo_path(detector_path))
        self.recognizer_path = Path(resolve_repo_path(recognizer_path))
        self.threshold = threshold
        self.enabled = enabled

    def ready(self) -> bool:
        return self.enabled and self.detector_path.is_file() and self.recognizer_path.is_file()

    def _decode(self, payload: bytes) -> np.ndarray | None:
        try:
            with Image.open(BytesIO(payload)) as opened:
                return cv2.cvtColor(np.asarray(opened.convert("RGB")), cv2.COLOR_RGB2BGR)
        except (UnidentifiedImageError, OSError, ValueError):
            return None

    def _face_feature(self, image: np.ndarray) -> tuple[np.ndarray | None, dict[str, Any] | None]:
        height, width = image.shape[:2]
        detector = cv2.FaceDetectorYN.create(str(self.detector_path), "", (width, height), 0.55, 0.3, 5000)
        _, faces = detector.detect(image)
        if faces is None or len(faces) == 0:
            return None, None
        face = max(faces, key=lambda row: float(row[2] * row[3]))
        recognizer = cv2.FaceRecognizerSF.create(str(self.recognizer_path), "")
        aligned = recognizer.alignCrop(image, face)
        feature = recognizer.feature(aligned).reshape(-1).astype(np.float32)
        norm = float(np.linalg.norm(feature))
        if norm:
            feature /= norm
        box = {"x": int(face[0]), "y": int(face[1]), "width": int(face[2]), "height": int(face[3]), "detector_score": round(float(face[-1]), 4)}
        return feature, box

    def verify(self, document_image: bytes, live_image: bytes | None, portrait_region: tuple[float, float, float, float]) -> dict[str, Any]:
        base = {
            "model": self.model_name,
            "model_version": self.model_version,
            "similarity_measure": "COSINE_SIMILARITY",
            "configured_prototype_threshold": self.threshold,
            "source": "LOCAL_PROTOTYPE_BIOMETRICS",
            "limitations": ["Prototype 1:1 verification is not production-certified border biometrics.", "The 0.55 prototype threshold separates the small synthetic golden fixtures but is not population or operational calibration."],
        }
        if not self.ready():
            return {**base, "status": "UNAVAILABLE", "decision": "UNAVAILABLE", "reason": "Local face model is disabled or missing.", "similarity": None}
        document = self._decode(document_image)
        if document is None:
            return {**base, "status": "UNAVAILABLE", "decision": "UNAVAILABLE", "reason": "Document image could not be decoded.", "similarity": None}
        h, w = document.shape[:2]
        x1, y1, x2, y2 = portrait_region
        portrait = document[int(y1 * h):int(y2 * h), int(x1 * w):int(x2 * w)]
        portrait_feature, portrait_box = self._face_feature(portrait)
        if portrait_feature is None:
            return {**base, "status": "UNAVAILABLE", "decision": "UNAVAILABLE", "reason": "No usable face was detected in the document portrait region.", "similarity": None}
        if not live_image:
            return {**base, "status": "UNAVAILABLE", "decision": "UNAVAILABLE", "reason": "A live or uploaded comparison face was not supplied.", "similarity": None, "document_face": portrait_box, "_embedding": portrait_feature.tolist()}
        live = self._decode(live_image)
        live_feature, live_box = self._face_feature(live) if live is not None else (None, None)
        if live_feature is None:
            return {**base, "status": "UNAVAILABLE", "decision": "UNAVAILABLE", "reason": "No usable face was detected in the comparison image.", "similarity": None, "document_face": portrait_box, "_embedding": portrait_feature.tolist()}
        similarity = float(np.dot(portrait_feature, live_feature))
        matched = similarity >= self.threshold
        return {
            **base,
            "status": "PASS" if matched else "FAIL",
            "decision": "MATCH" if matched else "MISMATCH",
            "reason": "Local face embeddings meet the prototype match threshold." if matched else "Local face embeddings do not meet the prototype match threshold.",
            "similarity": round(similarity, 6),
            "document_face": portrait_box,
            "comparison_face": live_box,
            "_embedding": portrait_feature.tolist(),
        }
