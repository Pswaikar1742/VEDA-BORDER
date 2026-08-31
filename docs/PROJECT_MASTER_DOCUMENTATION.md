# VEDA-BORDER: Master Project Documentation
**Verification & Evidence-Driven Autopsy for Border Identity & Document Screening**

[![SIH 2026 Problem Statement](https://img.shields.io/badge/SIH%202026-PS%2026188-blue.svg)](https://www.sih.gov.in/)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.11+-009688.svg)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014%20%7C%20TypeScript-000000.svg)](https://nextjs.org/)
[![Test Suite](https://img.shields.io/badge/Automated%20Tests-60%20Passed-brightgreen.svg)]()
[![Classification](https://img.shields.io/badge/Classification-Forensic%20Research%20Prototype-orange.svg)]()

---

## 1. Problem Statement & "WH" Framework Analysis

### **WHAT: What is VEDA-BORDER & What is Problem Statement 26188?**
* **Problem Statement:** SIH 2026 PS 26188 — *AI-Based Fake Identity & Document Screening System*.
* **The Core Challenge:** Border screening checkpoints face increasingly sophisticated fraud vectors: physically altered dates, swapped portraits, forged security features, fraudulent visas/stamps, identity impersonation, duplicate face biometrics across multiple aliases, and blacklisted/revoked documents.
* **The Solution — VEDA-BORDER:** An evidence-first, decision-support forensic screening platform powered by the **Identity Forensic Autopsy Engine (IFAE)**. 
* **Paradigm Shift:** Unlike standard black-box AI models that output an opaque "87% Fake" probability, VEDA-BORDER decomposes inspection into **independent evidence lanes**, records transparent cryptographic and physical provenance, applies a **4-Tier Authority Hierarchy**, detects hard cross-source contradictions, tracks multi-identity biometric linkage, and compiles an explainable **Identity Forensic Autopsy (IFA)** report for human immigration officers.

---

### **WHY: Why is an Evidence-First Forensic Autopsy Paradigm Required?**
1. **Opaque "Fake vs Real" Classifiers Fail at Borders:** A single neural network predicting "Real" or "Fake" cannot explain *which* specific field was forged or *why*. Border officers require legally defensible, actionable evidence (e.g., "MRZ Date of Birth checksum mismatch" or "Facial cosine similarity of 0.32 indicates portrait substitution").
2. **Deterministic Rules Must Never Be Overridden by AI:** If an ICAO 9303 MRZ checksum fails mathematically, no computer vision model should override it and declare the passport valid. Deterministic machine-readable invariants and cryptographic signatures must always hold higher authority than heuristic image scores.
3. **Zero Silent Passes (Coverage-Aware Safety):** In conventional systems, if a biometric or forensic service fails or experiences a network outage, it silently defaults to "Pass" or ignores the check. In VEDA-BORDER, missing mandatory evidence explicitly yields `INDETERMINATE`, preventing unauthorized entry during subsystem degradation.
4. **Explainable Decision Support:** The system is an officer decision-support workstation, not an autonomous gatekeeper. It leaves an indisputable, timestamped audit trail.

---

### **WHO: Who are the Stakeholders and Primary Users?**
* **Governing Body:** Ministry of Home Affairs (MHA), Government of India.
* **Operational Agency:** Sashastra Seema Bal (SSB), Police II Division.
* **End Users:**
  1. *Front-Line Immigration Officers:* Process passenger documents at border clearance booths in under 10 seconds with instant traffic-light triage (`LOW_RISK`, `REFER`, `HIGH_RISK`, `INDETERMINATE`) and actionable Next-Best-Evidence steps.
  2. *Secondary Inspection Forensic Examiners:* In-depth workstation review of suspicious specimens, interactive tamper heatmap bounding boxes, VIZ-MRZ contradiction matrices, and biometric cluster graphs.
  3. *Border Intelligence Analysts:* Monitoring multi-identity biometric clusters and identifying transnational identity recycling patterns.

---

### **WHERE: Where is VEDA-BORDER Deployed & Operational?**
* **Operational Environments:**
  * Primary land border Integrated Check Posts (ICPs) along international borders (e.g., India-Nepal, India-Bhutan).
  * International airport immigration arrival/departure counters.
  * Seaport and dry-port immigration clearance desks.
* **Deployment Architecture:**
  * **Edge-Ready & Air-Gapped:** Fully containerized (`docker compose up --build`) on local workstation hardware.
  * **Zero External Cloud Dependency:** Core OCR, MRZ parsing, local visual forensics, YuNet/SFace biometrics, and threat intelligence operate 100% locally with zero internet access or third-party cloud API requirements.

---

### **WHEN: When is VEDA-BORDER Triggered?**
* **Primary Trigger:** At the moment of physical credential presentation (Passport, Visa, National ID, Driving Licence) and optional live facial webcam capture.
* **Secondary Trigger:** During secondary forensic escalation, historical case audits, or batch intelligence watchlist reconciliations.

---

### **WHICH: Which Documents, Modalities, and Threats are Covered?**
* **Document Families:**
  * `TRAVEL_DOCUMENT` (ICAO Doc 9303 TD3 Passports, TD1/TD2 ID cards).
  * `VISA_PERMIT` (Entry visas, work permits, stamped endorsements).
  * `NATIONAL_ID` (National identification cards).
  * `DRIVING_LICENCE` (Transport/driving credentials).
* **Modalities Evaluated:**
  1. *Physical Document Pixels:* RGB images / PDF scans.
  2. *Machine-Readable Zone (MRZ):* TD1, TD2, TD3 format lines.
  3. *Visual Inspection Zone (VIZ):* Printed alphanumeric fields.
  4. *Live Biometric Face:* 1:1 Live selfie capture vs. Document portrait extraction.
  5. *Identity Linkage Graph:* 128-dimensional biometric vector gallery.
  6. *Threat Watchlists:* Synthetic/local intelligence lists (Lost/Stolen/Immigration alerts).

---

### **HOW: How Does VEDA-BORDER Work Technically?**
VEDA-BORDER processes documents through a multi-stage, fail-closed pipeline:
1. **Specimen Ingestion & Quality Gate:** Verifies image resolution, exposure, and sharpness before execution.
2. **Document Classification & Extraction:** Classifies family and extracts VIZ text and MRZ check digits.
3. **Deterministic & Visual Forensics:** Validates checksums, expiry rules, cross-field VIZ↔MRZ consistency, and analyzes high-frequency noise and edge gradients.
4. **Biometric Face Match & Vector Linkage:** Runs YuNet face detection and SFace 128-d cosine matching; checks for multi-identity face reuse.
5. **Adaptive Evidence Graph & Hypotheses:** Compiles findings into an authority-ranked DAG and formulates human-readable forensic hypotheses.
6. **Coverage Governor & Next-Best Action Planner:** Enforces hard gates and mandatory coverage, outputting the final triage outcome and step-by-step officer recommendations.

---

## 2. End-to-End Runtime Dataflow Architecture

```
                    DOCUMENT IMAGE + OPTIONAL LIVE SELFIE
                                      │
                                      ▼
                       1. Capture Quality Gate
                  (Sharpness, Exposure, Resolution)
                                      │ [PASS]
                                      ▼
                      2. Document Family Classifier
             (Travel Document, Visa, National ID, Licence)
                                      │
        ┌───────────────────┬─────────┴─────────┬───────────────────┐
        ▼                   ▼                   ▼                   ▼
   3. Visible OCR      4. ICAO MRZ       5. Local Visual      6. Biometric
   VIZ Extraction     Parser & Checks       Forensics        Face Match 1:1
   (Tesseract 5)      (7-3-1 Modulo-10)   (Noise / Edges)     (YuNet+SFace)
        │                   │                   │                   │
        └─────────┬─────────┘                   │                   │
                  ▼                             │                   │
         7. Cross-Source VIZ↔MRZ                │                   │
           Consistency Engine                   │                   │
                  │                             │                   │
        ┌─────────┴─────────┬───────────────────┴───────────────────┘
        ▼                   ▼
   8. Deterministic    9. Threat Watchlist &
     Validity Rules       Biometric Linkage
        │                   │
        └─────────┬─────────┘
                  ▼
   10. Adaptive Forensic Evidence Graph
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
   11. Forensic        12. Next-Best-Action
    Hypotheses              Planner
        │                   │
        └─────────┬─────────┘
                  ▼
   13. Coverage Governor & Hard Gates
                  │
                  ▼
   14. Identity Forensic Autopsy (IFA)
     (LOW_RISK | REFER | HIGH_RISK | INDETERMINATE)
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
   15. Case Storage    16. Workstation UI &
     & Export Engine     Audit Dossier
```

---

## 3. Comprehensive Module Inventory (All 20 Subsystems)

| # | Subsystem / Module | Source File | Core Technology / Library | Input Data | Output Artifacts | Evidence Tier |
|---|---|---|---|---|---|---|
| **1** | **Specimen Ingestion** | `services/api/app/validation.py` | Python `magic`, standard library | Raw HTTP upload payload | Validated image bytes, SHA-256 hash | Ingestion |
| **2** | **Capture Quality Gate** | `services/api/app/quality.py` | OpenCV Laplacian variance, histogram clipping | Document image bytes | Quality pass/fail, blur score, exposure metrics | **Tier 1 (Prerequisite)** |
| **3** | **Document Classifier** | `services/api/app/document_families.py` | Regex patterns, layout heuristics | OCR text tokens | Document family (`TRAVEL_DOCUMENT`, `VISA`, etc.) | Routing |
| **4** | **VIZ Text Extractor** | `services/api/app/extraction.py` | Local Tesseract 5.5.3 OCR engine | Document image bytes | Extracted names, DOB, document number, confidence | **Tier 2 / Tier 3** |
| **5** | **ICAO MRZ Parser** | `services/api/app/mrz.py` | ICAO Doc 9303 weighted modulo-10 (7-3-1) | MRZ image crop / raw text | Checksum verifications, parsed MRZ fields | **Tier 1 (Hard Gate)** |
| **6** | **Visual Forensics Lane** | `services/api/app/visual_forensics.py` | Laplacian edge analysis, high-frequency noise | Document image bytes | Tamper heatmaps, localized bounding boxes | **Tier 3 (Heuristic)** |
| **7** | **Biometric Face Match** | `services/api/app/biometrics.py` | OpenCV YuNet detector + SFace 128-d ONNX | Document crop + Live selfie | Cosine similarity score (Threshold: 0.55), match flag | **Tier 1 (Hard Gate)** |
| **8** | **Cross-Source Consistency** | `services/api/app/consistency.py` | Levenshtein distance, date normalizers | VIZ fields + MRZ fields | Field contradiction matrix (DOB, names, dates) | **Tier 1 / Tier 2** |
| **9** | **Validity & Expiry Rules** | `services/api/app/pipeline.py` | Python datetime, calendar logic | Extracted dates vs UTC clock | Expiry status, issuance interval validity | **Tier 2** |
| **10** | **Threat Intelligence** | `services/api/app/intelligence.py` | SQLite local watchlist fixtures | Document number, Holder name | Watchlist hits, alert categories, risk tier | **Tier 1 (Hard Gate)** |
| **11** | **Multi-Identity Linkage** | `services/api/app/linkage.py` | SFace vector store + cosine clustering | 128-d facial vector + Holder ID | Linked alias identities, cluster ID | **Tier 2** |
| **12** | **Evidence Graph Builder** | `services/api/app/evidence_graph.py` | Directed Acyclic Graph (DAG) model | All lane findings & provenance | Structured Evidence Graph nodes and edges | Aggregation |
| **13** | **Hypothesis Engine** | `services/api/app/policy.py` | Deterministic policy rules | Evidence Graph state | Primary forensic hypothesis & supporting evidence | Reasoning |
| **14** | **Next-Action Planner** | `services/api/app/policy.py` | Prioritized rule tree | Missing evidence / contradictions | Ranked investigation steps (e.g. `RECAPTURE_FIELD`) | Decision Support |
| **15** | **Coverage Governor** | `services/api/app/policy.py` | Hard gate invariants, coverage ratio | Evidence completeness metrics | Final triage outcome (`LOW_RISK`, `REFER`, etc.) | Policy Engine |
| **16** | **Autopsy Engine** | `services/api/app/autopsy.py` | Pydantic v2 schemas | Unified screening results | Standardized `IdentityForensicAutopsy` contract | Final Dossier |
| **17** | **Case Database Ledger** | `services/api/app/persistence.py` | SQLite3 with WAL mode | Complete case autopsy payload | Persistent case record, unique `case_id` | Storage |
| **18** | **Audit Report Generator** | `services/api/app/reporting.py` | Jinja2 / standard library | Stored case record | Printable HTML autopsy report and signed JSON | Reporting |
| **19** | **Forensic Workstation** | `apps/web/` | Next.js 14, TypeScript, Tailwind CSS | API JSON responses | Interactive UI, bounding box overlays, graphs | Frontend UI |
| **20** | **FastRouter Support** | `services/api/app/fastrouter_client.py` | HTTP client (`httpx`) to optional LLM | Verified evidence findings | Plain-English summary for officer review | **Tier 4 (Supportive)** |

---

## 4. The 4-Tier Authority & Truth Hierarchy

Evidence is organized into strict authority levels so that weaker, probabilistic signals can never override stronger, deterministic facts:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TIER 1: HARD GATES (Authoritative & Cryptographic Invariants)               │
│ • ICAO 9303 MRZ Checksum Contradictions                                      │
│ • Biometric Portrait Match Failures (Score < 0.55)                           │
│ • Threat Intelligence / Watchlist Hits                                       │
│ • Capture Quality Gate Failure (Severe blur, glare, insufficient resolution) │
│ RULE: Any Tier 1 failure immediately triggers REFER / HIGH_RISK triage.      │
├─────────────────────────────────────────────────────────────────────────────┤
│ TIER 2: DETERMINISTIC MACHINE-READABLE & CROSS-SOURCE INTEGRITY             │
│ • VIZ-to-MRZ Semantic Field Reconciliation (DOB, Expiry, Document Number)   │
│ • Document Expiry Date vs Current UTC Clock                                 │
│ • Multi-Identity Alias Linkage (Same face vector presented under aliases)   │
├─────────────────────────────────────────────────────────────────────────────┤
│ TIER 3: OBSERVED HEURISTIC FORENSICS & SIGNAL ANOMALIES                      │
│ • Local Laplacian Edge Variance Anomalies                                    │
│ • High-Frequency Noise Residual Discontinuities around Photo/Text Regions   │
├─────────────────────────────────────────────────────────────────────────────┤
│ TIER 4: SUPPORTIVE NATURAL LANGUAGE EXPLANATION (Optional / VLM)            │
│ • Plain-English summaries generated by FastRouter LLM adapter               │
│ RULE: Strictly supportive; cannot authenticate or override any check.        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Evidence Contracts & Triage Outcomes

### A. Mandatory Evidence States
Every analysis lane in VEDA-BORDER produces a strictly typed status:
* `PASS`: The evidence lane completed and found zero discrepancies.
* `FAIL`: The evidence lane completed and identified a hard contradiction or rule violation.
* `SUSPICIOUS`: The lane detected an anomalous signal requiring human officer adjudication.
* `UNAVAILABLE`: The lane could not run (e.g., hardware disabled, camera disconnected). **UNAVAILABLE is never normalized to PASS.**
* `NOT_APPLICABLE`: The lane is irrelevant for the specimen family (e.g., MRZ check on a non-MRZ domestic ID).

### B. Final Screening Triage Outcomes
The Coverage Governor evaluates the Evidence Graph and computes one of four outcomes:
1. **`LOW_RISK`**: All mandatory evidence lanes completed with `PASS`; no contradictions, expiry alerts, or watchlist hits.
2. **`REFER`**: Non-critical anomalies detected (e.g., local visual noise anomaly, expired document, multi-identity linkage cluster). Secondary inspection required.
3. **`HIGH_RISK`**: A critical hard gate triggered (e.g., Watchlist hit, VIZ-MRZ hard contradiction, MRZ checksum tampering, biometric face mismatch).
4. **`INDETERMINATE`**: Mandatory evidence is incomplete, capture quality failed, or a required lane is unavailable. Prevents unauthorized clearance during system degradation.

---

## 6. Scientific Verification & Benchmark Validation

VEDA-BORDER strictly follows academic and forensic standards, maintaining complete data isolation and transparently publishing benchmark baselines:

### 1. Internal Golden Test Scenarios (100% Passing)
* **Scenario A (Clean Travel Document):** All lanes PASS → `LOW_RISK`.
* **Scenario B (MRZ Checksum Tampered):** Checksum fails → `HIGH_RISK`.
* **Scenario C (VIZ-MRZ Cross-Source Contradiction):** DOB printed ≠ MRZ DOB → `HIGH_RISK`.
* **Scenario D (Biometric Face Mismatch):** Document portrait ≠ Live selfie → `HIGH_RISK`.
* **Scenario E (Threat Watchlist Hit):** Document number on mock blacklist → `HIGH_RISK`.
* **Scenario F (Multi-Identity Face Reuse):** Same face registered under another name → `REFER`.
* **Scenario G (Degraded / Low-Quality Specimen):** Quality gate fails → `INDETERMINATE`.
* **Scenario H (Expired Credential):** Expiry date < UTC now → `REFER`.
* **Scenario I (Provider Offline / Missing Lane):** Mandatory lane disabled → `INDETERMINATE`.

### 2. External Benchmark Baselines
Evaluated on published research datasets without training leakage:
* **MIDV-2020 (4,000 samples, 10 document types):** Tested OCR extraction, MRZ detection, and quality gates across scanned and mobile-captured modalities.
* **SIDTD (222 test samples, 10 classes):** Tested visual edge/noise tamper detection on physical identity document forgeries.
* **FantasyID (437 test samples):** Tested digital manipulation and copy-move forgery detection.
* **DLC-2021 (Diamond / L3i / Smart Engines):** Verification of document family classification adapters.

---

## 7. How to Run & Operate the Project

### A. One-Command Docker Launch (Zero Port Conflicts)
```bash
docker compose up --build
```
* **Frontend Workstation:** `http://localhost:3000`
* **Backend API Docs (Swagger):** `http://localhost:8000/docs`
* **API Health Check:** `http://localhost:8000/health`

**Custom Port Overrides (Avoid host port conflicts):**
```bash
API_PORT=8080 WEB_PORT=3080 NEXT_PUBLIC_API_URL=http://localhost:8080 docker compose up --build
```

### B. Local Development CLI Commands
```bash
# 1. Install dependencies
make api-install
make web-install

# 2. Generate test fixtures
make fixtures

# 3. Execute Pytest suite (60 tests)
make api-test

# 4. Run integrated Golden Scenario evaluations
make evaluate-integrated

# 5. Start Backend API
make api-run

# 6. Start Frontend Workstation
make web-run
```

---

## 8. REST API Specification

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/screenings` | Upload document (+ optional selfie) to execute complete forensic autopsy. |
| `GET` | `/api/v1/cases` | List all persisted screening cases and summary metrics. |
| `GET` | `/api/v1/cases/{case_id}` | Retrieve complete structured Identity Forensic Autopsy payload. |
| `GET` | `/api/v1/cases/{case_id}/report.html` | Export printable, officer-facing HTML autopsy report. |
| `GET` | `/api/v1/cases/{case_id}/report.json` | Export cryptographically verifiable JSON autopsy record. |
| `GET` | `/api/v1/identity-linkage` | Query biometric cluster ledger and linked multi-identity aliases. |
| `GET` | `/api/v1/system/status` | Real-time health status across all forensic subsystems. |
| `GET` | `/api/v1/fixtures` | Fetch available synthetic sample presets for 1-click loading. |
| `GET` | `/health` | Core API health check. |

---

## 9. Future Roadmap & Technical Evolution

1. **OCR V2 (Dynamic Polygon Quad-Warping):** Upgrading from static coordinate bounding boxes to dynamic 4-point perspective warping and deep text detection (DBNet/PaddleOCR) for skewed mobile captures.
2. **Visual Forensics V2 (Deep Learned Tamper Representations):** Incorporating self-supervised vision transformer models (e.g., Cat-Net / TruFor) trained on synthetic copy-move and splicing benchmarks.
3. **Hardware Biometric Liveness (3D Passive PAD):** Integrating ISO/IEC 30107-3 compliant passive presentation attack detection to prevent 2D photo and screen replay attacks.
4. **Physical ePassport / NFC Chip Reader Lane:** Interfacing with ISO 14443 contactless smart card readers to validate ICAO Doc 9303 Active Authentication and Passive Authentication (SOD hash signatures) against ICAO Master List trust chains.
5. **Government Backend Connectors:** Secure, authorized message queue connectors for MHA / SSB immigration backends, Interpol SLTD (Stolen and Lost Travel Documents), and C-FIMS.
