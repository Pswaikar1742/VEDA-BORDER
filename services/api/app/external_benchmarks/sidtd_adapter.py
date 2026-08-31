from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import List, Optional

from .base import ExternalBenchmarkAdapter, ExternalBenchmarkSample


class SIDTDAdapter(ExternalBenchmarkAdapter):
    """Adapter for Synthetic Dataset of ID and Travel Document (SIDTD)."""

    def __init__(self, root_dir: str | Path = "data/external/sidtd") -> None:
        super().__init__(root_dir)

    @property
    def benchmark_id(self) -> str:
        return "SIDTD"

    def is_available(self) -> bool:
        # Check if templates directory is extracted or zip is present
        templates_dir = self.root_dir / "templates" / "Images"
        splits_dir = self.root_dir / "splits" / "hold_out_split_templates" / "split_normal"
        if not splits_dir.is_dir():
            splits_dir = self.root_dir / "splits" / "split_normal"
        return (templates_dir.is_dir() or (self.root_dir / "templates.zip").is_file()) and splits_dir.is_dir()

    def list_splits(self) -> List[str]:
        return ["train", "val", "test"]

    def list_samples(self, split: str = "test") -> List[ExternalBenchmarkSample]:
        if split not in self.list_splits():
            raise ValueError(f"Unknown split '{split}'. Available: {self.list_splits()}")

        split_csv = self.root_dir / "splits" / "hold_out_split_templates" / "split_normal" / f"{split}_split_SIDTD.csv"
        if not split_csv.is_file():
            split_csv = self.root_dir / "splits" / "split_normal" / f"{split}_split_SIDTD.csv"
        if not split_csv.is_file():
            raise FileNotFoundError(f"Split CSV not found: {split_csv}")

        samples: List[ExternalBenchmarkSample] = []
        with open(split_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # image_path in csv is e.g. 'templates/Images/fakes/fin_id_00_fake_0_178.jpg'
                rel_img_path = row["image_path"].strip()
                full_path = self.root_dir / rel_img_path

                is_fake = int(row["label"]) == 1
                gt_class = "FORGERY" if is_fake else "BONAFIDE"

                class_name = row.get("class_name", "").strip()
                # Determine document family
                if "passport" in rel_img_path.lower():
                    doc_family = "TRAVEL_DOCUMENT"
                elif "id" in rel_img_path.lower():
                    doc_family = "NATIONAL_ID"
                elif "driver" in rel_img_path.lower() or "dl" in rel_img_path.lower():
                    doc_family = "DRIVING_LICENCE"
                else:
                    doc_family = "TRAVEL_DOCUMENT"

                # Extract base template ID (e.g. fin_id_00)
                fname = Path(rel_img_path).stem
                parts = fname.split("_fake_")
                base_doc_id = parts[0] if len(parts) > 1 else fname

                manip_type = None
                if is_fake:
                    # SIDTD uses inpainting and crop_and_replace techniques
                    manip_type = "inpainting_or_crop_replace"

                samples.append(
                    ExternalBenchmarkSample(
                        benchmark_id=self.benchmark_id,
                        sample_id=rel_img_path,
                        source_path=str(full_path),
                        document_family=doc_family,
                        ground_truth_class=gt_class,
                        manipulation_type=manip_type,
                        document_id=base_doc_id,
                        split=split,
                        annotations={
                            "class_name": class_name,
                            "class_index": int(row.get("class", -1)),
                            "label_name": row.get("label_name", ""),
                        },
                        source_metadata={
                            "official_source": "TC-11 / Computer Vision Center (CVC)",
                            "split_protocol": "split_normal",
                        },
                    )
                )

        return samples
