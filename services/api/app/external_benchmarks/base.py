from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ExternalBenchmarkSample:
    """Normalized external benchmark sample record."""

    benchmark_id: str
    sample_id: str
    source_path: str
    document_family: str
    ground_truth_class: str  # 'BONAFIDE', 'FORGERY', 'PRESENTATION_ATTACK'
    manipulation_type: Optional[str] = None  # 'crop_and_replace', 'inpainting', 'face_swap', etc.
    subject_id: Optional[str] = None
    document_id: Optional[str] = None
    video_id: Optional[str] = None
    split: str = "test"  # 'train', 'val', 'test'
    annotations: Dict[str, Any] = field(default_factory=dict)
    source_metadata: Dict[str, Any] = field(default_factory=dict)

    def read_bytes(self) -> bytes:
        return Path(self.source_path).read_bytes()


class ExternalBenchmarkAdapter(ABC):
    """Abstract interface for external benchmark adapters."""

    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)

    @property
    @abstractmethod
    def benchmark_id(self) -> str:
        """Return the unique benchmark identifier."""
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if dataset files are downloaded and accessible locally."""
        raise NotImplementedError

    @abstractmethod
    def list_samples(self, split: str = "test") -> List[ExternalBenchmarkSample]:
        """Return list of normalized samples for the specified split."""
        raise NotImplementedError

    @abstractmethod
    def list_splits(self) -> List[str]:
        """Return available official splits."""
        raise NotImplementedError


def calculate_binary_classification_metrics(
    y_true: List[int],  # 0 = negative/bonafide, 1 = positive/forgery or attack
    y_pred: List[int],
    y_scores: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """Calculate standard binary classification metrics without external scikit-learn dependency."""
    if len(y_true) != len(y_pred):
        raise ValueError(f"Mismatch in length: y_true={len(y_true)}, y_pred={len(y_pred)}")

    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)

    total = len(y_true)
    accuracy = (tp + tn) / total if total > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0  # Sensitivity / TPR
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0  # TNR
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    balanced_accuracy = 0.5 * (recall + specificity)

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    return {
        "sample_count": total,
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1_score": f1,
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
        "confusion_matrix": {
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
        },
    }
