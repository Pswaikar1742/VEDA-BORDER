from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import ExternalBenchmarkAdapter, ExternalBenchmarkSample


class MIDV2020Adapter(ExternalBenchmarkAdapter):
    """Adapter for MIDV-2020 identity document dataset (La Rochelle University / Smart Engines)."""

    def __init__(self, root_dir: str | Path = "data/external/midv-2020") -> None:
        super().__init__(root_dir)
        self._annotation_cache: Dict[str, Dict[str, Any]] = {}

    @property
    def benchmark_id(self) -> str:
        return "MIDV-2020"

    def is_available(self) -> bool:
        # Check if any modality folder exists with images
        for mod in ["templates", "scan_upright", "scan_rotated", "photo"]:
            img_dir = self.root_dir / mod / "images"
            if img_dir.is_dir() and any(img_dir.iterdir()):
                return True
        return False

    def list_splits(self) -> List[str]:
        return ["templates", "scan_upright", "scan_rotated", "photo", "all"]

    def _load_annotations(self, modality: str, doctype: str) -> Dict[str, Any]:
        cache_key = f"{modality}/{doctype}"
        if cache_key in self._annotation_cache:
            return self._annotation_cache[cache_key]

        ann_file = self.root_dir / modality / "annotations" / f"{doctype}.json"
        if not ann_file.is_file():
            return {}

        try:
            with open(ann_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                meta = data.get("_via_img_metadata", {})
                self._annotation_cache[cache_key] = meta
                return meta
        except Exception:
            return {}

    def list_samples(self, split: str = "all") -> List[ExternalBenchmarkSample]:
        if not self.is_available():
            return []

        modality_map = {
            "templates": ["templates"],
            "scan_upright": ["scan_upright"],
            "scans": ["scan_upright"],
            "scan_rotated": ["scan_rotated"],
            "photo": ["photo"],
            "photos": ["photo"],
            "all": ["templates", "scan_upright", "scan_rotated", "photo"],
        }

        modalities = modality_map.get(split.lower())
        if modalities is None:
            raise ValueError(f"Unknown split '{split}'. Available: {self.list_splits()}")

        samples: List[ExternalBenchmarkSample] = []
        img_extensions = {".jpg", ".jpeg", ".png", ".tif"}

        for mod in modalities:
            mod_img_dir = self.root_dir / mod / "images"
            if not mod_img_dir.is_dir():
                continue

            for doctype_dir in sorted(mod_img_dir.iterdir()):
                if not doctype_dir.is_dir():
                    continue

                doctype = doctype_dir.name
                doc_family = "TRAVEL_DOCUMENT" if "passport" in doctype.lower() else "NATIONAL_ID"
                ann_meta = self._load_annotations(mod, doctype)

                for img_path in sorted(doctype_dir.glob("*")):
                    if img_path.suffix.lower() not in img_extensions or not img_path.is_file():
                        continue

                    rel_path = img_path.relative_to(self.root_dir)
                    img_name = img_path.name
                    doc_id = f"{doctype}_{img_path.stem}"

                    # Extract VIA field annotations for this image if available
                    fields: Dict[str, Any] = {}
                    for key, entry in ann_meta.items():
                        if entry.get("filename") == img_name:
                            for region in entry.get("regions", []):
                                r_attr = region.get("region_attributes", {})
                                f_name = r_attr.get("field_name")
                                f_val = r_attr.get("value", "")
                                if f_name:
                                    fields[f_name] = {
                                        "value": f_val,
                                        "shape": region.get("shape_attributes", {}),
                                    }
                            break

                    samples.append(
                        ExternalBenchmarkSample(
                            benchmark_id=self.benchmark_id,
                            sample_id=str(rel_path),
                            source_path=str(img_path),
                            document_family=doc_family,
                            ground_truth_class="BONAFIDE",
                            manipulation_type="unaltered_mock",
                            document_id=doc_id,
                            split=mod,
                            annotations={
                                "modality": mod,
                                "document_type": doctype,
                                "sample_index": img_path.stem,
                                "fields": fields,
                            },
                            source_metadata={
                                "official_source": "L3i Laboratory, La Rochelle University & Smart Engines",
                                "official_access": "OFFICIAL_SFTP_APPROVED",
                                "license": "CC-BY-SA-2.5",
                            },
                        )
                    )

        return samples
