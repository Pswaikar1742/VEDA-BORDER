# Integrated Research Prototype Completion Report

VEDA-BORDER is the research prototype implementation for Smart India Hackathon 2026 Problem Statement **PS 26188: AI-Based Fake Identity & Document Screening System** (Ministry of Home Affairs / Sashastra Seema Bal, Police II Division).

This sprint completed the full transition from isolated task-level demos to the **Complete Integrated VEDA-BORDER Research Prototype Workstation**.

---

## 1. Inherited State & What Was Stabilized

- **Inherited baseline commit:** `c658e942143a45b5d39523d7798f151cfaced16c` (Task 04).
- **Inherited uncommitted work from Codex:** Partially scaffolded modules for quality, biometrics, visual forensics, linkage, evidence graph, policy, integrated pipeline, and workspace routes.
- **Actions taken:**
  - Audited all inherited files, verified OpenCV YuNet and SFace model assets and license files (`SFACE_LICENSE`, `YUNET_LICENSE`).
  - Resolved model and database path resolution across the entire engine via `resolve_repo_path`.
  - Added full typing and fields to Pydantic contracts (`triage_risk_index`, `triage_risk_label`, `audit_trail`, `limitations`).
  - Upgraded Next.js from vulnerable `14.2.5` to patched `14.2.35` in `apps/web/package.json`.
  - Created complete 22-test integrated prototype test suite (`services/api/tests/test_integrated_prototype.py`).
  - Built evaluation runner (`services/api/tools/evaluate_integrated.py`) for all 9 Golden Scenarios.
  - Replaced the plain legacy upload page with a complete, modern, government-tech forensic workstation UI (`apps/web/`).

---

## 2. Core Implemented Modules

### A. Document Family Routing (`document_families.py`)
- Supported families: `TRAVEL_DOCUMENT` (Passport/TD3), `VISA_OR_PERMIT`, `NATIONAL_ID`, `DRIVING_LICENCE`.
- Automatic classification via pixel OCR markers with manual override capability.
- Non-MRZ families evaluate MRZ validation as `NOT_APPLICABLE` (never `PASS` or `FAIL`).

### B. Capture Quality Gate (`quality.py`)
- Evaluates resolution (>= 700x440), sharpness variance of Laplacian (>= 45.0), mean brightness (45–220), dark/bright clipping, and document edge density.
- Halts downstream analysis and requests `RECAPTURE_DOCUMENT` if quality checks fail.

### C. 1:1 Biometric Face Verification (`biometrics.py`)
- Pinned local OpenCV YuNet (`face_detection_yunet_2023mar.onnx`) and SFace (`face_recognition_sface_2021dec.onnx`).
- 128-dimensional embedding cosine similarity.
- Prototype threshold: `0.55` (strictly separates synthetic fixtures: same face ~0.948, different face ~0.405).
- Documented as prototype policy, not operational population calibration.

### D. Local Visual Forensics (`visual_forensics.py`)
- Deterministic high-frequency noise & edge residual profile grid analysis.
- Layout-specific portrait region anomaly check (edge robust z >= 2.65).
- ORB keypoint descriptor copy-move / duplicate region detection.
- JPEG recompression residual measurement.

### E. Multi-Identity Biometric Linkage (`linkage.py`)
- SQLite-backed embedding store (`LocalIdentityLinkageStore`).
- Detects shared face vectors (similarity >= 0.50) claiming conflicting names or document numbers.
- Groups records into `Biometric Cluster XXX` and flags `POSSIBLE_MULTI_IDENTITY_LINKAGE` / `SUSPICIOUS`.

### F. Adaptive Evidence Graph & 4-Tier Authority Hierarchy (`evidence_graph.py`)
- Graph representation of Claims vs Independent Evidence Nodes.
- 4-Tier Authority Hierarchy (Tier 1: Chip/Govt > Tier 2: MRZ/Rules/Watchlist > Tier 3: VIZ/Forensics > Tier 4: Biometrics/Linkage).
- Contradiction policy: lower numeric tiers override higher numeric tiers; PASS scores are never averaged to cancel hard contradictions.

### G. Forensic Hypothesis Engine (`policy.py`)
- Deterministic hypothesis synthesis:
  - `POSSIBLE_VISIBLE_BIOGRAPHIC_FIELD_ALTERATION`
  - `POSSIBLE_PORTRAIT_SUBSTITUTION`
  - `POSSIBLE_DOCUMENT_REGION_MANIPULATION`
  - `POSSIBLE_MULTI_IDENTITY_USAGE`
  - `DOCUMENT_STATUS_ALERT`
  - `INSUFFICIENT_FORENSIC_COVERAGE`
  - `NO_CURRENT_CROSS_SOURCE_CONTRADICTION`

### H. Next-Best-Evidence Action Planner (`policy.py`)
- Prioritized verification recommendations (`RECAPTURE_DOCUMENT`, `RECAPTURE_FIELD_REGION`, `CAPTURE_HIGHER_RESOLUTION_REGION`, `RUN_VISUAL_FORENSICS`, `CAPTURE_LIVE_FACE`, `REFER_TO_SECONDARY_INSPECTION`, `READ_ELECTRONIC_CREDENTIAL`) with explicit justifications of WHY.

### I. Coverage Governor, Hard Gates, and Triage Outcome (`policy.py`, `autopsy.py`)
- Missing mandatory evidence strictly returns `INDETERMINATE`.
- Active hard gates enforce `HIGH_RISK`.
- Outcomes: `LOW_RISK`, `REFER`, `HIGH_RISK`, `INDETERMINATE`.
- Emits explicit `triage_risk_index` (e.g. 8.0, 55.0, 90.0) with disclaimer.

### J. Persistence, Reporting, and Workstation API (`persistence.py`, `reporting.py`, `routes/workspace.py`)
- Local SQLite case repository (`cases` table).
- Professional printable HTML forensic autopsy reports (`GET /api/v1/cases/{id}/report.html`).
- Machine-readable JSON autopsy export (`GET /api/v1/cases/{id}/report.json`).
- Diagnostic healthcheck endpoint (`GET /api/v1/system/status`) covering all 11 modules.

### K. Next.js Forensic Workstation UI (`apps/web/`)
- Professional government-tech information-dense layout.
- Views: Dashboard, New Screening, Case Ledger, Identity Linkage Graph, System Status, Policy & Settings.
- Features: Drag & Drop upload, webcam capture for document & live face, 1-click test fixture presets, interactive SVG Evidence Graph viewer, and Visual Forensics bounding-box overlays.

---

## 3. Golden Scenario Evaluation Matrix

Evaluated via `services/api/tools/evaluate_integrated.py` against `data/integrated_fixtures/`:

| Scenario | Description | Expected Outcome | Observed Outcome | Coverage | Hard Gates Triggered | Status |
|---|---|---|---|---|---|:---:|
| **A** | Clean Travel Credential + Matching Live Face | `LOW_RISK` | `LOW_RISK` | COMPLETE | None | **PASS** |
| **B** | Visible Date of Birth Alteration (VIZ != MRZ) | `HIGH_RISK` | `HIGH_RISK` | COMPLETE | `CRITICAL_CROSS_SOURCE_CONTRADICTION` | **PASS** |
| **C** | Portrait Region Substitution / Tamper Cue | `REFER` | `REFER` | COMPLETE | None (Visual Forensic Suspicious) | **PASS** |
| **D** | Expired Travel Credential | `REFER` | `REFER` | COMPLETE | `EXPIRED_DOCUMENT` | **PASS** |
| **E** | Local Prototype Watchlist Blacklist Hit | `HIGH_RISK` | `HIGH_RISK` | COMPLETE | `LOCAL_PROTOTYPE_WATCHLIST_HIT` | **PASS** |
| **F** | Biometric Face Mismatch (Live Face != Portrait) | `HIGH_RISK` | `HIGH_RISK` | COMPLETE | `REQUIRED_BIOMETRIC_MISMATCH` | **PASS** |
| **G** | Multi-Identity Linkage (Shared Face, Conflicting Claims) | `SUSPICIOUS Linkage` | `SUSPICIOUS` | COMPLETE | `LOCAL_PROTOTYPE_WATCHLIST_HIT` | **PASS** |
| **H** | Threat Intelligence Offline / Unavailable | `INDETERMINATE` | `INDETERMINATE` | INCOMPLETE | `MANDATORY_EVIDENCE_INCOMPLETE` | **PASS** |
| **I** | Degraded / Poor Capture Quality (Blur/Low-Res) | `INDETERMINATE` | `INDETERMINATE` | INCOMPLETE | `MANDATORY_EVIDENCE_INCOMPLETE` | **PASS** |

**Result:** 9 / 9 Scenarios Passed (100%).

---

## 4. Verification Results

- **Backend Pytest Suite:** 48 tests passed (`python3 -m pytest -q services/api/tests`).
  - 26 baseline tests (Task 01–04)
  - 22 integrated prototype tests
- **Integrated Golden Scenario Evaluator:** 9 passed out of 9 (`python3 services/api/tools/evaluate_integrated.py`).
- **Task 04 Image Benchmark Evaluator:** 25 specimens evaluated (`python3 services/api/tools/evaluate_task04.py`).
- **Frontend Production Build:** Compiled successfully with Next.js 14.2.35 (`npm run build` in `apps/web`).

---

## 5. Model Assets & Licences

| Asset | File | Size | SHA-256 | Licence |
|---|---|---|---|---|
| Face Detection | `face_detection_yunet_2023mar.onnx` | 232.6 KB | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` | BSD-3-Clause (`YUNET_LICENSE`) |
| Face Embeddings | `face_recognition_sface_2021dec.onnx` | 38.7 MB | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79` | Apache 2.0 (`SFACE_LICENSE`) |

---

## 6. Exact Startup Commands

```bash
# Terminal 1: Backend
make api-install
make fixtures
make evaluate-integrated
make api-test
make api-run

# Terminal 2: Frontend
make web-install
make web-build
make web-run
```

Open `http://localhost:3000` to interact with the complete VEDA-BORDER Workstation.
