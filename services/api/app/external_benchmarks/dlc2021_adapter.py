from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import ExternalBenchmarkAdapter, ExternalBenchmarkSample


class DLC2021Adapter(ExternalBenchmarkAdapter):
    """Adapter for Document Liveness Challenge 2021 (DLC-2021)."""

    def __init__(self, root_dir: str | Path = "data/external/dlc-2021") -> None:
        super().__init__(root_dir)

    @property
    def benchmark_id(self) -> str:
        return "DLC-2021"

    def is_available(self) -> bool:
        return (self.root_dir / "dlc-2021.csv").is_file()

    def list_splits(self) -> List[str]:
        return ["all", "screen_test", "graycopy_test", "unlaminated_test"]

    def list_samples(self, split: str = "all") -> List[ExternalBenchmarkSample]:
        csv_path = self.root_dir / "dlc-2021.csv"
        if not csv_path.is_file():
            raise FileNotFoundError(f"DLC-2021 index CSV not found: {csv_path}")

        samples: List[ExternalBenchmarkSample] = []
        with open(csv_path, mode="r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or ";" not in line:
                    continue
                parts = line.split(";")
                clip_id = parts[0].strip()  # e.g. alb_id/00.cc0001
                device = parts[1].strip() if len(parts) > 1 else ""
                condition = parts[2].strip() if len(parts) > 2 else ""

                # Parse document template and attack type from clip_id
                # e.g. alb_id/00.cc0001 -> doc_id = 'alb_id/00', attack = 'cc'
                doc_path_part, clip_filename = clip_id.split("/") if "/" in clip_id else ("", clip_id)
                prefix_code = clip_filename.split(".")[1] if "." in clip_filename else clip_filename

                attack_code = ""
                for code in ["or", "cg", "cc", "re"]:
                    if code in prefix_code:
                        attack_code = code
                        break

                if attack_code == "or":
                    gt_class = "BONAFIDE"
                    manip_type = "original_mock"
                elif attack_code == "cg":
                    gt_class = "PRESENTATION_ATTACK"
                    manip_type = "grayscale_copy"
                elif attack_code == "cc":
                    gt_class = "PRESENTATION_ATTACK"
                    manip_type = "color_copy"
                elif attack_code == "re":
                    gt_class = "PRESENTATION_ATTACK"
                    manip_type = "screen_recapture"
                else:
                    gt_class = "UNKNOWN"
                    manip_type = "unknown"

                doc_family = "TRAVEL_DOCUMENT" if "passport" in clip_id.lower() else "NATIONAL_ID"
                doc_id = f"{doc_path_part}/{clip_filename.split('.')[0]}" if "." in clip_filename else doc_path_part

                samples.append(
                    ExternalBenchmarkSample(
                        benchmark_id=self.benchmark_id,
                        sample_id=clip_id,
                        source_path=str(self.root_dir / f"{clip_id}.mp4"),
                        document_family=doc_family,
                        ground_truth_class=gt_class,
                        manipulation_type=manip_type,
                        document_id=doc_id,
                        split=split,
                        annotations={
                            "device": device,
                            "condition": condition,
                            "attack_code": attack_code,
                        },
                        source_metadata={
                            "official_source": "Zenodo (DOI: 10.5281/zenodo.7467028)",
                            "journal": "Journal of Imaging (DOI: 10.3390/jimaging8070181)",
                        },
                    )
                )

        return samples
