from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import ExternalBenchmarkAdapter, ExternalBenchmarkSample


class MIDV2020Adapter(ExternalBenchmarkAdapter):
    """Adapter for MIDV-2020 identity document dataset (La Rochelle University / Smart Engines)."""

    def __init__(self, root_dir: str | Path = "data/external/midv-2020") -> None:
        super().__init__(root_dir)

    @property
    def benchmark_id(self) -> str:
        return "MIDV-2020"

    def is_available(self) -> bool:
        # Check if annotations or images directory exists
        return (self.root_dir / "annotations").is_dir() or (self.root_dir / "images").is_dir()

    def list_splits(self) -> List[str]:
        return ["scans", "photos", "video_frames", "all"]

    def list_samples(self, split: str = "all") -> List[ExternalBenchmarkSample]:
        if not self.is_available():
            return []

        samples: List[ExternalBenchmarkSample] = []
        img_extensions = {".png", ".jpg", ".jpeg", ".tif"}
        for img_path in sorted(self.root_dir.rglob("*")):
            if img_path.suffix.lower() not in img_extensions or not img_path.is_file():
                continue

            rel_path = img_path.relative_to(self.root_dir)
            doc_family = "TRAVEL_DOCUMENT" if "passport" in str(rel_path).lower() else "NATIONAL_ID"
            doc_id = img_path.parent.name

            samples.append(
                ExternalBenchmarkSample(
                    benchmark_id=self.benchmark_id,
                    sample_id=str(rel_path),
                    source_path=str(img_path),
                    document_family=doc_family,
                    ground_truth_class="BONAFIDE",
                    manipulation_type="unaltered_mock",
                    document_id=doc_id,
                    split=split,
                    annotations={},
                    source_metadata={
                        "official_source": "La Rochelle University / Smart Engines",
                        "official_access": "WAITING_FOR_HUMAN_ACCESS",
                    },
                )
            )

        return samples
