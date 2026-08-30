# VEDA-BORDER: Verification & Evidence-Driven Autopsy for Border Identity Forensics

> **Official SIH 2026 Problem Statement:** PS 26188 — AI-Based Fake Identity & Document Screening System<br>
> **Organization:** Ministry of Home Affairs / Sashastra Seema Bal (SSB), Police II Division<br>
> **Core Engine:** Identity Forensic Autopsy Engine (IFAE)<br>
> **Deployment Philosophy:** INDIA-FIRST, GLOBALLY EXTENSIBLE<br>
> **Classification:** Research Prototype

VEDA-BORDER is an evidence-first forensic screening workstation that replaces single-score "fake vs real" classifiers with an **Adaptive Forensic Evidence Graph**, a strict **4-Tier Authority Hierarchy**, cross-source contradiction reconstruction, biometric linkage, and policy-driven triage outcomes.

---

## Key Capabilities & Innovations

1. **Adaptive Forensic Evidence Graph:** Maintains independent evidence claims across physical, machine-readable, and biometric layers.
2. **4-Tier Truth Hierarchy:** Lower numeric tiers hold higher authority (Tier 1: Chip/Govt > Tier 2: MRZ/Rules/Watchlist > Tier 3: VIZ/Forensics > Tier 4: Biometrics/Linkage). Strong contradictions cannot be averaged away by weak PASS scores.
3. **Forensic Hypothesis Engine:** Deterministically synthesizes multi-lane evidence into structured hypotheses (e.g. `POSSIBLE_VISIBLE_BIOGRAPHIC_FIELD_ALTERATION`, `POSSIBLE_PORTRAIT_SUBSTITUTION`, `POSSIBLE_MULTI_IDENTITY_USAGE`).
4. **Next-Best-Evidence Action Planner:** Tells the border officer exactly what verification action to perform next (e.g. `RECAPTURE_FIELD_REGION`, `CAPTURE_LIVE_FACE`, `REFER_TO_SECONDARY_INSPECTION`) with explicit justifications of WHY.
5. **Coverage Governor & Hard Gates:** Missing mandatory evidence is strictly preserved as `INDETERMINATE`, never converted to `PASS`. Critical contradictions trigger hard screening gates (`HIGH_RISK`).
6. **Multi-Identity Biometric Linkage:** Employs local 128-dimensional face embeddings to discover clusters of conflicting identities claiming different names or document numbers with the same face.
7. **Extensible Document Families:** Supports `TRAVEL_DOCUMENT` (Passports/TD3), `VISA_OR_PERMIT`, `NATIONAL_ID`, and `DRIVING_LICENCE` without hardcoding country-specific assumptions.
8. **1:1 Face Verification:** Local OpenCV YuNet face detection and SFace feature extraction with cosine similarity comparison against live webcam or uploaded comparison faces.
9. **Visual Forensics & Overlay:** Local high-frequency noise and edge residual heuristics with visual bounding-box overlays on suspect regions.
10. **Case Persistence & Audit Reporting:** SQLite-backed case ledger with printable HTML forensic autopsies and cryptographic JSON exports.

---

## Local Requirements

- Python 3.11+
- Tesseract 5 with English language pack
- Node.js 18+ & npm
- `pdftoppm` (poppler-utils) for PDF support

---

## Quickstart & Evaluation Commands

### 1. Backend Setup & Tests

```bash
# Install dependencies
make api-install

# Generate integrated synthetic fixtures
make fixtures

# Run Golden Scenarios evaluation (Scenarios A through I)
make evaluate-integrated

# Run full backend test suite (48 tests)
make api-test

# Start FastAPI server on port 8000
make api-run
```

### 2. Frontend Workstation

In a second terminal:

```bash
# Install frontend dependencies
make web-install

# Verify production build
make web-build

# Start Next.js development server on port 3000
make web-run
```

Open `http://localhost:3000` to launch the **VEDA-BORDER Forensic Workstation**.

---

## API Endpoints

- `POST /api/v1/screenings`: Execute complete multi-modal forensic autopsy on document + optional selfie.
- `GET /api/v1/cases`: Retrieve case ledger list and outcome summary counts.
- `GET /api/v1/cases/{case_id}`: Retrieve detailed case autopsy.
- `GET /api/v1/cases/{case_id}/report.html`: Printable HTML forensic autopsy report.
- `GET /api/v1/cases/{case_id}/report.json`: Cryptographic JSON autopsy export.
- `GET /api/v1/identity-linkage`: Query multi-identity biometric clusters.
- `GET /api/v1/system/status`: Real-time readiness check for all 11 modules.
- `GET /api/v1/fixtures`: List synthetic test presets for 1-click loading.
- `GET /health`: Healthcheck.

---

## Scientific & Ethical Boundaries

- **Research Prototype:** All credentials, numbers, names, and watchlist entries in the repository are synthetic and fictional.
- **No Operational Database Connection:** Does not access Indian Passport Seva, MHA, SSB, ICAO PKD, or INTERPOL databases.
- **Policy-Driven Triage:** Triage outcomes (`LOW_RISK`, `REFER`, `HIGH_RISK`, `INDETERMINATE`) and the Triage Risk Index are decision-support classifications, not calibrated mathematical probabilities of fraud.
