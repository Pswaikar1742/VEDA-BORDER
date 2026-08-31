from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import ExternalBenchmarkAdapter, ExternalBenchmarkSample


class FantasyIDAdapter(ExternalBenchmarkAdapter):
    """Adapter for FantasyID dataset (Idiap Research Institute / ICCV 2025 DeepID Challenge)."""

    def __init__(self, root_dir: str | Path = "data/external/fantasyid") -> None:
        super().__init__(root_dir)

    @property
    def benchmark_id(self) -> str:
        return "FantasyID"

    def is_available(self) -> bool:
        csv_path = self.root_dir / "FantasyID" / "test.csv"
        return csv_path.is_file()

    def list_splits(self) -> List[str]:
        return ["train", "test", "hindi_subset"]

    def list_samples(self, split: str = "test") -> List[ExternalBenchmarkSample]:
        base_dir = self.root_dir / "FantasyID"
        csv_file = base_dir / "test.csv" if split in {"test", "hindi_subset"} else base_dir / "train.csv"

        if not csv_file.is_file():
            raise FileNotFoundError(f"FantasyID split CSV not found: {csv_file}")

        import csv
        samples: List[ExternalBenchmarkSample] = []
        with open(csv_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rel_path = row["path"].strip()
                full_path = base_dir / rel_path

                is_attack = row["is_attack"].strip().lower() == "true"
                gt_class = "FORGERY" if is_attack else "BONAFIDE"
                attack_type = row.get("attack_type", "none").strip()

                path_str = rel_path.lower()
                lang = "unknown"
                for l_code in ["hin", "hindi", "ara", "chi", "fra", "per", "por", "rus", "tur", "ukr", "eng", "sgp", "nld", "hkg", "chinese", "french", "russian", "german", "spanish"]:
                    if l_code in path_str:
                        lang = l_code
                        break

                if split == "hindi_subset" and lang not in {"hin", "hindi"}:
                    continue

                doc_family = "TRAVEL_DOCUMENT" if "passport" in path_str else "NATIONAL_ID"
                doc_id = Path(rel_path).stem

                samples.append(
                    ExternalBenchmarkSample(
                        benchmark_id=self.benchmark_id,
                        sample_id=rel_path,
                        source_path=str(full_path),
                        document_family=doc_family,
                        ground_truth_class=gt_class,
                        manipulation_type=attack_type if is_attack else "bonafide_template",
                        document_id=doc_id,
                        split=split,
                        annotations={
                            "language": lang,
                            "attack_type": attack_type,
                        },
                        source_metadata={
                            "official_source": "Idiap Research Institute (Zenodo DOI: 10.34777/c966-nn94)",
                            "license": "CC-BY-4.0",
                        },
                    )
                )

        return samples
