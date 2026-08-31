# VEDA-BORDER — Internal Round Build Freeze

**Project:** VEDA-BORDER  
**Expansion:** Verification & Evidence-Driven Autopsy for Border Identity and Document Screening  
**Problem Statement:** SIH 2026 PS 26188: AI-Based Fake Identity & Document Screening System  
**Core Engine:** Identity Forensic Autopsy Engine (IFAE)  
**Classification:** Research Prototype  
**Freeze Date:** 2026-09-01  
**Build Status:** FROZEN / READY FOR PRESENTATION  
**Git HEAD:** `3907aad545ba2b83597c554580fbcf2c575aa9be`  
**Git Tag:** `internal-round-2026-09-01`  

---

## 1. Executive Summary & Build State

VEDA-BORDER is an evidence-first forensic document and identity screening platform built for frontline border control checkpoints. Unlike opaque black-box "fake vs real" classifiers, VEDA-BORDER constructs an explainable, multi-tiered forensic evidence graph over physical, cryptographic, semantic, and biometric signals.

This document formally freezes the **Internal Round Build** for presentation and evaluation.

---

## 2. Working Prototype Modules

| Subsystem | Module Name | Implementation Source | Operational State | Evidence Tier |
|---|---|---|---|---|
| **Ingestion** | Specimen Ingestion & Validation | `services/api/app/validation.py` | ACTIVE | Ingestion |
| **Quality Gate** | Capture Quality Assessment | `services/api/app/quality.py` | ACTIVE | Tier 1 (Prerequisite) |
| **Document Family** | Document Classification | `services/api/app/document_families.py` | ACTIVE | Routing |
| **OCR Lane** | Visible Zone Text Extraction | `services/api/app/extraction.py` | ACTIVE | Tier 2 / Tier 3 |
| **MRZ Lane** | Deterministic ICAO MRZ Parser | `services/api/app/mrz.py` | ACTIVE | Tier 1 (Hard Gate) |
| **Rules Engine** | Family-Aware Expiry & Validity Rules | `services/api/app/pipeline.py` | ACTIVE | Tier 2 |
| **Consistency** | Cross-Source Semantic Consistency | `services/api/app/consistency.py` | ACTIVE | Tier 1 / Tier 2 |
| **Visual Forensics** | Local Visual Noise & Edge Forensics | `services/api/app/visual_forensics.py` | ACTIVE (V1 Heuristics) | Tier 3 |
| **Biometrics** | YuNet + SFace Face Verification | `services/api/app/biometrics.py` | ACTIVE (ONNX 1:1) | Tier 1 (Hard Gate) |
| **Intelligence** | Prototype Threat Watchlist | `services/api/app/intelligence.py` | ACTIVE (Local Prototype) | Tier 1 (Hard Gate) |
| **Linkage** | Multi-Identity Linkage Ledger | `services/api/app/linkage.py` | ACTIVE (SQLite Embeddings) | Tier 2 |
| **Evidence Graph** | Adaptive Forensic Evidence Graph | `services/api/app/evidence_graph.py` | ACTIVE | Aggregation |
| **Hypothesis** | Forensic Hypothesis Engine | `services/api/app/policy.py` | ACTIVE | Reasoning |
| **Planner** | Next-Best-Evidence Planner | `services/api/app/policy.py` | ACTIVE | Decision Support |
| **Governor** | Coverage Governor & Hard Gates | `services/api/app/policy.py` | ACTIVE | Policy Enforcement |
| **Autopsy** | Identity Forensic Autopsy Engine | `services/api/app/autopsy.py` | ACTIVE | Final Evidence Trail |
| **Persistence** | Case Database & Audit Ledger | `services/api/app/persistence.py` | ACTIVE (SQLite) | Storage |
| **Reporting** | Audit Report & Export Generator | `services/api/app/reporting.py` | ACTIVE (JSON/Text) | Reporting |
| **Workstation UI** | Next.js 14 Forensic Workstation | `apps/web/` | ACTIVE (TypeScript/React) | UI / Presentation |
| **LLM Provider** | Optional FastRouter Adapter | `services/api/app/fastrouter_client.py` | ACTIVE (Optional/Disabled) | Tier 4 (Supportive) |

---

## 3. Internal Verification Test Results

- **Backend Test Suite (`pytest services/api/tests`):** **60 / 60 tests passed (100%)**
  - API endpoint contracts: 3 tests
  - Benchmark & fixture coverage: 6 tests
  - Leakage & split isolation: 5 tests
  - Pydantic v2 evidence contracts: 3 tests
  - FastRouter provider degradation: 4 tests
  - Integrated prototype end-to-end: 22 tests
  - Prediction boundary enforcement: 3 tests
  - MRZ & extraction validation: 6 tests
  - Consistency & visual forensics: 8 tests
- **Integrated Golden Scenarios (`evaluate_integrated.py`):** **9 / 9 scenarios passed (100%)**
- **Frontend Production Build (`npm run build`):** **Compiled successfully (0 errors, 4/4 static pages generated)**

---

## 4. External Benchmark Baselines (Frozen)

VEDA-BORDER enforces scientific integrity by evaluating against four independent published benchmarks with strictly isolated prediction boundaries:

### A. MIDV-2020 External Baseline V1 (4,000 samples, 10 document types, 4 modalities)
- **Substring OCR Match (Text Found):** **50.71%** (Passports: 55.55%, National IDs: 42.92%)
- **Structured Field Exact Match:** **0.00%** (Static crop & English regex limitation)
- **Mean Character Error Rate (CER):** **93.33%**
- **MRZ Detection Rate (Travel Documents):** **7.81%** (Templates: **31.25%**)
- **MRZ Checksum Pass Rate (Detected):** **67.20%** (84/125 valid check digits)
- **Capture Quality Gate Pass Rate:** **46.35%** (Templates: 100%, Photos: 85.4%, Scans: 0.0%)
- **Localization:** `UNSUPPORTED` (Static heuristics, no bounding-box model)
- **Throughput:** **2.97 samples/sec** (4,000 samples in 1,345.5 s)

### B. SIDTD External Baseline V1 (222 test samples, 10 classes)
- **Accuracy:** **52.25%**
- **Balanced Accuracy:** **54.48%**
- **Precision:** **62.90%**
- **Recall:** **31.97%**
- **Specificity:** **77.00%**
- **F1 Score:** **0.4239**
- **False Negative Rate:** **68.03%**

### C. FantasyID External Baseline V1 (437 test samples)
- **Accuracy:** **42.34%**
- **Balanced Accuracy:** **49.53%**
- **Precision:** **65.92%**
- **Recall:** **27.96%**
- **Specificity:** **71.09%**
- **F1 Score:** **0.3927**

### D. DLC-2021 (Diamond / L3i / Smart Engines)
- Metadata, split manifest, and test adapters integrated and verified.

---

## 5. Known Limitations & Roadmap for Next Iteration

1. **Visual Forensics Generalization (Visual Forensics V2):** Current V1 visual forensics uses localized edge and noise heuristics tuned for high-contrast digital specimens. It generalizes weakly on real photographic scans (SIDTD 52.25%, FantasyID 42.34%). Visual Forensics V2 (learned deep tamper representations) is designated for post-internal iteration.
2. **OCR & Document Localization (OCR V2):** Current V1 OCR uses static coordinate crop zones and English-centric header regexes. It requires dynamic polygon quad-warping, orientation deskewing, and multi-lingual layout analysis for real-world border checkpoints.
3. **Hardware & Biometric Liveness:** Biometric verification operates as 1:1 facial recognition using ONNX YuNet + SFace. Passive/active 3D liveness detection remains simulated via capture quality checks.
4. **Threat Intelligence:** Threat intelligence operates against a local prototype watchlist database rather than live INTERPOL/NCIC feeds.
