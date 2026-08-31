# Dataset Ledger

This ledger records all internal and external datasets, provenance, licensing, access statuses, and leakage controls.

| Dataset Identifier | Purpose | Official Source / Publisher | Licence / Terms | Access Status | Raw / Extracted Size | PII / Sensitivity | Split Strategy | VEDA Usage |
|---|---|---|---|---|---|---|---|---|
| **Synthetic VEDA Fixtures v2** | Task 01–04 integration tests, golden cases, failure injection, UI demos | In-repo generator (`generate_integrated_fixtures.py`) | Project-owned | `AVAILABLE` | ~15 MB | Entirely fictional synthetic data | Deterministic seeds; evaluation truth loaded only after frozen predictions | Integration & Golden Suite Only |
| **SIDTD (Templates + Splits)** | Primary external forgery & manipulation benchmark | TC-11 / CVC Universitat Autònoma de Barcelona | Open Research / CVC Terms | `DOWNLOADED` | 1.2 GB / ~1.4 GB | Synthetic mock IDs (MIDV-2020 derived) | Official `split_normal` (Train: 2511, Val: 313, Test: 315) | External Forgery Evaluation |
| **FantasyID** | Multi-language digital forgery (Hindi, French, English, etc.) | Idiap Research Institute (Zenodo DOI: 10.34777/c966-nn94) | `CC-BY-4.0` | `DOWNLOADED` | 2.4 GB / ~2.6 GB | Synthetic / Fantasy ID cards | Language & template disjoint validation/test | Digital Manipulation Benchmark |
| **DLC-2021 (Metadata & Baseline)** | Physical presentation attack detection (original, copies, screen recapture) | Smart Engines / MDPI / Zenodo (DOI: 10.5281/zenodo.7467028) | `CC-BY-SA-2.5` | `METADATA_AND_BASELINE_DOWNLOADED` | 84.4 MB (Raw video corpus 99 GB) | Synthetic IDs / artificial personal information | Official split lists (`graycopy`, `screen`, `unlaminated`) | Physical Liveness Benchmark |
| **MIDV-2020** | Mobile document localization, field extraction & OCR robustness under capture variations | L3i, La Rochelle University / Smart Engines | `CC-BY-SA-2.5` | `DOWNLOADED` | 6.7 GB / ~7.5 GB (4,000 images across 4 modalities) | Synthetic mock IDs / Generated Photos | Modality & template disjoint partitions (`templates`, `scans`, `photos`) | OCR & Localization Robustness |
| **MIDV-Holo** | Dynamic hologram & optical variable security feature research | Smart Engines | Research Release | `DEFERRED` | ~15 GB | Synthetic / research credentials | Video sequence disjoint | Optional Future Research |
| **ICAO Doc 9303** | International Standard for MRZ check digits & travel document specifications | International Civil Aviation Organization (ICAO) | International Standard (Free access) | `AVAILABLE` | N/A (Standard Specification) | Official Specifications | Standard specifications (Not a dataset) | Deterministic MRZ Rule Validation |

---

## Prediction Boundary Invariants
1. Runtime modules accept only raw decoded specimen bytes.
2. Runtime modules NEVER receive ground truth class, manipulation type, split annotations, or ground truth metadata.
3. Benchmark evaluation runner freezes runtime predictions before loading ground truth annotations for scoring.
4. Internal golden suite results are strictly separated from external benchmark metrics.
