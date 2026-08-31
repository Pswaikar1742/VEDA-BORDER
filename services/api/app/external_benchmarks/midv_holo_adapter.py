from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import ExternalBenchmarkAdapter, ExternalBenchmarkSample


class MIDVHoloAdapter(ExternalBenchmarkAdapter):
    """Adapter for MIDV-Holo dataset for dynamic security feature & hologram research."""

    def __init__(self, root_dir: str | Path = "data/external/midv-holo") -> None:
        super().__init__(root_dir)

    @property
    def benchmark_id(self) -> str:
        return "MIDV-Holo"

    def is_available(self) -> bool:
        return self.root_dir.is_dir() and any(self.root_dir.iterdir())

    def list_splits(self) -> List[str]:
        return ["all", "hologram_clips"]

    def list_samples(self, split: str = "all") -> List[ExternalBenchmarkSample]:
        if not self.is_available():
            return []

        samples: List[ExternalBenchmarkSample] = []
        for media_path in sorted(self.root_dir.rglob("*")):
            if media_path.suffix.lower() not in {".mp4", ".avi", ".png", ".jpg"} or not media_path.is_file():
                continue

            rel_path = media_path.relative_to(self.root_dir)
            samples.append(
                ExternalBenchmarkSample(
                    benchmark_id=self.benchmark_id,
                    sample_id=str(rel_path),
                    source_path=str(media_path),
                    document_family="TRAVEL_DOCUMENT",
                    ground_truth_class="BONAFIDE",
                    manipulation_type="hologram_security_feature",
                    document_id=media_path.stem,
                    split=split,
                    annotations={},
                    source_metadata={
                        "official_source": "Smart Engines / MIDV-Holo Repository",
                        "status": "DEFERRED",
                    },
                )
            )

        return samples
