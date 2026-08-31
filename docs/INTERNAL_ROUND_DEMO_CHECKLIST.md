# VEDA-BORDER — Internal Round Demo Checklist

**Presentation Date:** 2026-09-01  
**Build:** Internal Round Frozen Build  
**Location of Fixtures:** `data/integrated_fixtures/`  

---

## 1. Startup Commands

### Terminal 1 — FastAPI Backend (Port 8000)
```bash
uvicorn app.main:app --app-dir services/api --port 8000 --reload
```

### Terminal 2 — Next.js Workstation UI (Port 3000)
```bash
npm --prefix apps/web run dev
```

### Health & Readiness Check
Open browser to `http://localhost:3000` or run:
```bash
curl -s http://localhost:8000/api/system/status | jq .
```
*Expected: `"status": "READY"`, all core forensic modules active.*

---

## 2. Six Core Presentation Demo Scenarios

All demonstration fixtures are available in `data/integrated_fixtures/`.

### Scenario 1: Authentic Clean Travel Document
- **Specimen Image:** `data/integrated_fixtures/travel_clean.png`
- **Live Selfie Image:** `data/integrated_fixtures/ari_selfie.png`
- **Expected Outcome:** **`LOW_RISK`**
- **Evidence Highlights to Point Out to Judges:**
  - Full evidence coverage ($100\%$ mandatory lanes pass).
  - MRZ checks: 4/4 passed (composite, DOB, expiry, doc number checksums).
  - Biometric face verification: match score $\ge 0.85$ (green pass).
  - Evidence Graph shows all green Tier 1 and Tier 2 verified nodes.
  - Final Autopsy confirms authentic status with complete audit trail.

---

### Scenario 2: Semantic VIZ-vs-MRZ Tamper Contradiction
- **Specimen Image:** `data/integrated_fixtures/travel_dob_altered.png`
- **Live Selfie Image:** `data/integrated_fixtures/ari_selfie.png`
- **Expected Outcome:** **`REFER` (Selective Review)**
- **Evidence Highlights to Point Out to Judges:**
  - VIZ date of birth was physically altered from `1990-05-12` to `1998-05-12`.
  - Deterministic MRZ checksum validates authentic birthdate `900512`.
  - Cross-Source Consistency Engine flags **CRITICAL MISMATCH** between VIZ and MRZ.
  - Next-Best-Evidence Planner prioritizes: *"Re-read the conflicting region: date_of_birth"*.

---

### Scenario 3: Biometric Portrait Replacement Attack
- **Specimen Image:** `data/integrated_fixtures/travel_portrait_replaced.png`
- **Live Selfie Image:** `data/integrated_fixtures/lio_selfie.png`
- **Expected Outcome:** **`REFER` (Hard Gate Triggered)**
- **Evidence Highlights to Point Out to Judges:**
  - Imposter attempts entry using another individual's document.
  - OpenCV YuNet detector extracts document portrait and live selfie.
  - SFace 128d cosine distance score $< 0.55$ fails the biometric threshold.
  - **Tier 1 Biometric Hard Gate triggers unconditionally**, bypassing any heuristic scores.

---

### Scenario 4: Degraded Capture Quality (Frontline Indeterminate)
- **Specimen Image:** `data/integrated_fixtures/travel_poor_capture.png`
- **Live Selfie Image:** None / optional
- **Expected Outcome:** **`INDETERMINATE` / `MANUAL_REVIEW_REQUIRED`**
- **Evidence Highlights to Point Out to Judges:**
  - Capture quality gate flags heavy blur (Laplacian variance $< 100$) and severe glare.
  - Platform strictly refuses to make a fake/real classification on insufficient evidence.
  - Next-Best-Evidence Planner instructs officer: *"Recapture document under uniform lighting"*.

---

### Scenario 5: National Threat Intelligence Watchlist Hit
- **Specimen Image:** `data/integrated_fixtures/travel_blacklisted.png`
- **Live Selfie Image:** `data/integrated_fixtures/ari_selfie.png`
- **Expected Outcome:** **`HIGH_RISK` / `INTERCEPT`**
- **Evidence Highlights to Point Out to Judges:**
  - Document number matches active INTERPOL red notice watch entry.
  - **Tier 1 Intelligence Hard Gate triggers immediately**.
  - Autopsy displays immediate officer warning with protocol actions.

---

### Scenario 6: Multi-Identity Alias Linkage Attack
- **Step A:** Screen `data/integrated_fixtures/travel_clean.png` with `ari_selfie.png` (stores facial embedding in ledger).
- **Step B:** Screen `data/integrated_fixtures/national_id.png` (different name) with `ari_selfie_variant.png`.
- **Expected Outcome:** **`REFER` / `SUSPICIOUS` (Alias Linkage Alert)**
- **Evidence Highlights to Point Out to Judges:**
  - Multi-Identity Linkage Engine performs cosine search across historical SQLite cases.
  - Detects that the same facial biometric is associated with multiple conflicting identities.

---

## 3. UI Navigation Walkthrough for Presentation

1. **Dashboard Header:** Point out active system status (`READY`), local execution mode, and research prototype disclaimers.
2. **Interactive Screening Panel:** Drag and drop fixture images, select document family, and click *"Run Forensic Screening"*.
3. **Adaptive Evidence Graph:** Click nodes to expand evidence tiers (Tier 1 Hard Gates $\rightarrow$ Tier 2 Consistency $\rightarrow$ Tier 3 Heuristics).
4. **Forensic Hypothesis Engine:** Show judges the primary forensic hypothesis and competing hypotheses.
5. **Next-Best-Evidence Planner:** Highlight actionable, ranked recommendations for frontline border officers.
6. **Case Persistence & Export:** Click *"View Audit Dossier"* to inspect the stored SQLite case and export the complete autopsy report.
