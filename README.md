# VEDA-BORDER: Verification & Evidence-Driven Autopsy for Border Identity Forensics

[![SIH 2026](https://img.shields.io/badge/SIH%202026-Problem%20PS%2026188-blue.svg)](https://www.sih.gov.in/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Pydantic%20v2-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014%20%2B%20TypeScript-000000.svg)](https://nextjs.org/)
[![Tests](https://img.shields.io/badge/Tests-55%20Passed-brightgreen.svg)]()
[![Licence](https://img.shields.io/badge/License-Apache%202.0%20%2F%20Research%20Prototype-orange.svg)]()

> **Official SIH 2026 Problem Statement:** PS 26188 — AI-Based Fake Identity & Document Screening System  
> **Organization:** Ministry of Home Affairs / Sashastra Seema Bal (SSB), Police II Division  
> **Core Engine:** Identity Forensic Autopsy Engine (IFAE)  
> **Deployment Philosophy:** India-First, Globally Extensible  
> **Classification:** Forensic Screening & Decision-Support Research Prototype  

---

## 1. Executive Summary

Border identity inspection requires verifiable, multi-modal forensic evidence rather than opaque "black-box" classifiers. Real-world fraud ranges from subtle visual tampering and portrait substitution to synthetic identity fabrication and multi-identity face reuse across jurisdictions.

**VEDA-BORDER** (*Verification & Evidence-Driven Autopsy for Border Identity Forensics*) is a modular, evidence-first screening workstation and decision-support engine designed to meet the rigorous operational standards of border control authorities.

Rather than relying on a single "fake vs real" probability score, VEDA-BORDER constructs an **Adaptive Forensic Evidence Graph** across independent forensic lanes, applies a **4-Tier Authority Hierarchy**, detects hard cross-source contradictions, tracks multi-identity biometric linkage, and generates an explainable **Identity Forensic Autopsy (IFA)** report for front-line and secondary inspection officers.

---

## 2. Core Architectural Pillars

```
                     DOCUMENT IMAGE + OPTIONAL LIVE SELFIE
                                       │
                         ┌─────────────┴─────────────┐
                         ▼                           ▼
                 Capture Quality Gate         Tesseract OCR Engine
                         │                           │
                         ▼                           ▼
             Document Classifier ────────► Field & MRZ Extractor
                         │                           │
         ┌───────────────┼───────────────┬───────────┴───────────────┐
         ▼               ▼               ▼                           ▼
  ICAO 9303 MRZ    Deterministic   Local Visual    1:1 Face Biometrics &
  Check-Digits     Document Rules    Forensics     Multi-Identity Linkage
         │               │               │                   │
         └───────────────┼───────────────┴───────────────────┘
                         ▼
        Cross-Source Consistency (VIZ vs MRZ)
                         │
                         ▼
        Threat Intelligence / Watchlist Lookup
                         │
                         ▼
           ADAPTIVE FORENSIC EVIDENCE GRAPH
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
  Coverage Governor &             Forensic Hypothesis
     Hard Gates                          Engine
         │                               │
         └───────────────┬───────────────┘
                         ▼
           Next-Best-Evidence Action Planner
                         │
                         ▼
             FINAL FORENSIC AUTOPSY (IFA)
         (LOW_RISK | REFER | HIGH_RISK | INDETERMINATE)
```

### 1. 4-Tier Authority Hierarchy
Evidence sources are strictly stratified so that lower-tier PASS scores cannot cancel out higher-tier contradictions:
- **Tier 1 (Highest Authority):** Cryptographic Electronic Chip (`eMRTD`), Active Authentication, Authorized Government Backends.
- **Tier 2:** Deterministic ICAO Doc 9303 MRZ checksums, Document Validity Rules, Local Watchlists.
- **Tier 3:** Visual Inspection Zone (VIZ) OCR, Local Visual Forensics, Document Portrait extraction.
- **Tier 4:** 1:1 Live Face Biometric Verification, Identity Linkage Graph.

### 2. Deterministic Integrity & Cross-Source Consistency
- **ICAO 9303 Parser:** Validates TD1, TD2, and TD3 formats with weighted modulo-10 (7-3-1 weighting) check digits across document number, birth date, expiry date, and composite lines.
- **VIZ-MRZ Reconciler:** Field-by-field cross-comparison between the visible visual zone and machine-readable zone. Critical discrepancies (name, DOB, document number) trigger immediate hard gates.
- **Document Rules Engine:** Verifies date formats, future expiry dates, valid birth dates, and issuance intervals deterministically.

### 3. Visual Forensics & Tamper Localization
- Local high-frequency noise residual analysis (Gaussian difference) and Laplacian edge anomaly profiling over an adaptive grid.
- ORB keypoint descriptor clustering for duplicate region (copy-move / cloning) detection.
- Bounding-box coordinate generation for overlaying suspicious regions on the document visualizer.

### 4. 1:1 Face Verification & Multi-Identity Linkage
- **Local Biometrics:** OpenCV YuNet face detection + SFace 128-dimensional deep feature extraction (`ONNX` runtime, zero external API dependency).
- **Identity Linkage Store:** SQLite-backed vector ledger with cosine distance clustering to detect cross-case identity recycling (same physical face presented under distinct biographic claims).

### 5. Coverage Governor & Strict Hard Gates
- **Zero Silent Passes:** Missing mandatory evidence is strictly classified as `INDETERMINATE`, never converted to `PASS`.
- **Policy Gates:** Hard triggers for critical VIZ-MRZ contradictions, watchlist alerts, expired credentials, and verified biometric mismatches.

### 6. Autonomous Hypothesis Engine & Next-Best Action Planner
- Synthesizes multi-lane evidence into human-readable forensic hypotheses (e.g., `POSSIBLE_VISIBLE_BIOGRAPHIC_FIELD_ALTERATION`, `POSSIBLE_PORTRAIT_SUBSTITUTION`, `POSSIBLE_MULTI_IDENTITY_USAGE`).
- Provides actionable, prioritized recommendations for border officers (e.g., `RECAPTURE_FIELD_REGION`, `CAPTURE_LIVE_FACE`, `REFER_TO_SECONDARY_INSPECTION`).

---

## 3. Standardized External Benchmark Integration

VEDA-BORDER integrates official loaders and evaluators for leading open-source international forensic benchmarks with **zero runtime ground-truth leakage**:

| Benchmark | Official Source | Focus Area | Dataset Status |
|---|---|---|---|
| **SIDTD** | TC-11 / Computer Vision Center (CVC) | Synthetic ID Document Tampering (Inpainting, Crop-and-Replace) | Integrated & Evaluated |
| **FantasyID** | Idiap Research Institute (ICCV 2025 DeepID) | Multi-Language ID Digital Manipulation (13 Language Templates) | Integrated & Evaluated |
| **DLC-2021** | Smart Engines / Journal of Imaging | Document Liveness & Physical Presentation Attack Detection | Baseline Integrated |
| **MIDV-2020** | L3i, La Rochelle University | Perspective Variation, Mobile Video & Field OCR Robustness | Ingestion Protocol Ready |

---

## 4. Repository Structure

```
VEDA-Border/
├── apps/
│   └── web/                            # Next.js 14 Frontend Workstation
│       ├── app/                        # App Router (page.tsx, layout.tsx)
│       ├── components/                 # UI components (DocumentVisualizer, EvidenceGraphViewer, Navbar)
│       ├── lib/                        # TypeScript API client & shared contract types
│       ├── package.json
│       └── tsconfig.json
│
├── services/
│   └── api/                            # FastAPI Python Backend
│       ├── app/                        # Core backend application modules
│       │   ├── main.py                 # FastAPI application entrypoint & routing
│       │   ├── integrated_pipeline.py  # End-to-end multi-modal screening pipeline
│       │   ├── contracts.py            # Pydantic v2 schemas and evidence models
│       │   ├── evidence_graph.py       # Evidence graph constructor & tier resolver
│       │   ├── policy.py               # Hard gates, coverage governor & hypotheses
│       │   ├── visual_forensics.py     # Local image forensics & tamper detection
│       │   ├── biometrics.py           # OpenCV YuNet + SFace face verification
│       │   ├── linkage.py              # Identity linkage store & cluster search
│       │   ├── mrz.py                  # ICAO 9303 MRZ parser & checksum engine
│       │   ├── consistency.py          # VIZ vs MRZ cross-source reconciler
│       │   ├── extraction.py           # Tesseract OCR & layout extraction
│       │   ├── quality.py              # Image capture quality assessment
│       │   ├── validation.py           # Document rule validation engine
│       │   ├── document_families.py    # Family classification adapters
│       │   ├── persistence.py          # SQLite case persistence ledger
│       │   ├── reporting.py            # HTML and JSON autopsy report generators
│       │   ├── system_status.py        # System health & module readiness checks
│       │   └── external_benchmarks/    # Adapters for SIDTD, FantasyID, DLC-2021
│       │
│       ├── assets/                     # Pretrained ONNX models & face fixtures
│       │   ├── models/                 # face_detection_yunet, face_recognition_sface
│       │   └── licenses/               # Third-party model open-source licenses
│       │
│       ├── tests/                      # Automated Pytest Suite (55 tests)
│       │   ├── test_api.py             # API endpoint integration tests
│       │   ├── test_integrated_prototype.py # Full multi-modal pipeline tests
│       │   ├── test_contracts.py       # Pydantic schema validation tests
│       │   ├── test_benchmark_leakage.py # Dataset split leakage tests
│       │   ├── test_prediction_boundary.py # Runtime ground-truth isolation tests
│       │   ├── test_benchmark.py       # Benchmark evaluation tests
│       │   ├── test_task03.py          # Document rule & MRZ unit tests
│       │   └── test_task04.py          # Consistency & watchlist unit tests
│       │
│       ├── tools/                      # CLI evaluation and generator tools
│       │   ├── evaluate_external_benchmarks.py # SIDTD & FantasyID evaluator
│       │   ├── evaluate_integrated.py  # Golden scenario evaluation suite
│       │   └── generate_integrated_fixtures.py # Synthetic fixture builder
│       │
│       └── requirements.txt            # Python dependencies
│
├── data/
│   ├── integrated_fixtures/            # Pre-generated synthetic document test presets
│   ├── synthetic_benchmark/            # Synthetic test specimen suite
│   ├── evaluations/                    # Evaluation output reports and metrics
│   ├── external/                       # External dataset manifests and split definitions
│   └── runtime/                        # Local SQLite database directory (.gitkeep)
│
├── docs/                               # Engineering & Architectural Specifications
│   ├── ACCEPTANCE_TESTS.md             # Quality criteria & test requirements
│   ├── ARCHITECTURE.md                 # System architecture and dataflow
│   ├── BUILD_SPEC.md                   # Build specification and design rules
│   ├── DATASET_LEDGER.md               # Dataset provenance, licenses, and checksums
│   ├── DECISION_LOG.md                 # Engineering decision rationale
│   ├── EVIDENCE_CONTRACTS.md           # Typed API and schema contracts
│   ├── EXTERNAL_DATASETS.md            # Standardized external benchmark protocols
│   └── THREAT_MODEL.md                 # Border identity fraud threat analysis
│
├── AGENTS.md                           # Contributor & Agent Guidelines
├── Makefile                            # Unified build & evaluation automation
├── .env.example                        # Environment configuration template
├── .gitignore                          # Git ignore rules
└── README.md                           # Primary documentation
```

---

## 5. Getting Started & Installation

### Prerequisites
- **Python:** Version 3.11 or higher
- **Node.js:** Version 18 or higher (with npm)
- **Tesseract OCR:** Version 5 with English language pack installed
  - *Ubuntu/Debian:* `sudo apt-get install tesseract-ocr tesseract-ocr-eng libgl1 libglib2.0-0`
  - *macOS:* `brew install tesseract`
  - *Fedora/RHEL:* `sudo dnf install tesseract tesseract-langpack-eng`

### Step 1: Clone the Repository
```bash
git clone https://github.com/Pswaikar1742/VEDA-BORDER.git
cd VEDA-BORDER
```

### Step 2: Backend Setup
```bash
# Install Python dependencies
make api-install

# Generate synthetic fixtures
make fixtures

# Run the test suite
make api-test
```

### Step 3: Frontend Setup
```bash
# Install frontend dependencies
make web-install

# Verify production build
make web-build
```

---

## 6. Running the System

### Start the Backend API Server
```bash
make api-run
```
The FastAPI backend will start at `http://localhost:8000`.  
Interactive Swagger documentation is available at `http://localhost:8000/docs`.

### Start the Frontend Forensic Workstation
In a second terminal window:
```bash
make web-run
```
The Next.js workstation will start at `http://localhost:3000`.

---

## 7. Running Evaluations & Tests

| Command | Description |
|---|---|
| `make api-test` | Executes the complete Pytest suite (55 automated tests). |
| `make evaluate-integrated` | Runs end-to-end evaluation across all Golden Test Scenarios (A through I). |
| `make evaluate-external` | Evaluates visual forensics on SIDTD and FantasyID standardized external benchmarks. |
| `make test` | Runs both unit tests and integrated golden evaluations. |

---

## 8. API Specification

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/screenings` | Execute complete multi-modal forensic autopsy on document + optional selfie. |
| `GET` | `/api/v1/cases` | List all persisted screening cases and summary metrics. |
| `GET` | `/api/v1/cases/{case_id}` | Retrieve full Identity Forensic Autopsy for a specific case. |
| `GET` | `/api/v1/cases/{case_id}/report.html` | Export formatted printable HTML forensic autopsy report. |
| `GET` | `/api/v1/cases/{case_id}/report.json` | Export signed, cryptographic JSON autopsy data. |
| `GET` | `/api/v1/identity-linkage` | Query multi-identity biometric clusters and face similarity matches. |
| `GET` | `/api/v1/system/status` | Real-time health and readiness status across all 11 forensic subsystems. |
| `GET` | `/api/v1/fixtures` | Fetch available synthetic sample presets for 1-click workstation loading. |
| `GET` | `/health` | Basic API health check. |

---

## 9. Scientific, Ethical & Legal Boundaries

- **Research Prototype:** VEDA-BORDER is an evidence-first research and decision-support prototype. All identity credentials, names, numbers, and watchlist entries included in the repository are synthetic and fictional.
- **No Operational Government Database Connectivity:** The prototype does not connect to live Indian Passport Seva, MHA, SSB, ICAO PKD, or INTERPOL databases. Threat intelligence lookups use deterministic local fixtures.
- **Policy-Driven Triage:** Screening outcomes (`LOW_RISK`, `REFER`, `HIGH_RISK`, `INDETERMINATE`) and risk indices are policy-driven decision-support classifications based on completed evidence coverage, not mathematical fraud probabilities.
- **Human-in-the-Loop:** All automated findings are designed to provide an explainable evidence trail to assist authorized human border officers in making lawful immigration decisions.

---

## 10. License

Developed for the **Smart India Hackathon (SIH) 2026**.  
Distributed under standard open-source academic/research licensing. Pretrained ONNX biometric models (YuNet and SFace) are licensed under their respective Apache 2.0 / OpenCV terms (see `services/api/assets/licenses/`).
