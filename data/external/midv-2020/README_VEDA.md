# MIDV-2020 Dataset Integration in VEDA-BORDER

## Overview
MIDV-2020 provides 1,000 unique mock identity documents across 10 national document formats, each with synthetic faces, variable biographic text fields, and dense polygon annotations for text fields, photo regions, and signatures.

## Local Inventory
- `templates/`: 1,000 canonical digital template renderings + 10 VIA JSON schemas.
- `scan_upright/`: 1,000 flatbed scanner captures (upright orientation) + 10 VIA JSON schemas.
- `scan_rotated/`: 1,000 flatbed scanner captures (rotated orientation) + 10 VIA JSON schemas.
- `photo/`: 1,000 real-world smartphone photo captures (Samsung Galaxy S10 and Apple iPhone XR) under 8 environmental variations (low light, glare, cluttered backgrounds, projective distortion) + 10 VIA JSON schemas.

## Usage in VEDA-BORDER
Ingested via `MIDV2020Adapter` (`services/api/app/external_benchmarks/midv2020_adapter.py`) to benchmark:
1. Capture Quality assessment (glare, blur, lighting, skew).
2. OCR field extraction accuracy against ground-truth JSON values.
3. Document classification and boundary localization.
