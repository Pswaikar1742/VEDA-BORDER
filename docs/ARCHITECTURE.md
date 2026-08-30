# Architecture v2.0 — Integrated Forensic Research Prototype

## Core End-to-End Pipeline

```text
Specimen Pixels (PNG/JPG/PDF) [+ Optional Live Face]
  │
  ├─► 1. Capture Quality Gate (Sharpness, Resolution, Brightness, Clipping, Crop)
  │      └─► If Unacceptable: Stop downstream analysis -> Request RECAPTURE_DOCUMENT
  │
  ├─► 2. Document Family Classification (Travel Document, Visa/Permit, National ID, Driving Licence)
  │
  ├─► 3. Visible Document Extraction (Local Tesseract 5.5.3 OCR -> VIZ Fields & Confidence)
  │
  ├─► 4. Machine-Readable Zone Verification (TD3 Parser -> ICAO 7-3-1 Check Digits)
  │      └─► Non-MRZ families: Evaluated as NOT_APPLICABLE
  │
  ├─► 5. Deterministic Document Validity Rules (Calendar validity, Expiry, Mandatory fields)
  │
  ├─► 6. Cross-Source Consistency Reconstruction (VIZ <-> MRZ semantic comparison)
  │      └─► Contradictions flagged with CRITICAL / HIGH severity
  │
  ├─► 7. Local Visual Forensics (Local noise/edge profile, portrait edge anomaly, copy-move)
  │
  ├─► 8. Biometric 1:1 Face Verification (OpenCV YuNet detection + SFace 128-d cosine similarity @ 0.55)
  │
  ├─► 9. Local Threat Intelligence (LOCAL PROTOTYPE WATCHLIST lookup)
  │
  ├─► 10. Multi-Identity Biometric Linkage (SQLite embedding store -> cluster conflict detection)
  │
  ├─► 11. Adaptive Forensic Evidence Graph (Claims, Evidence Nodes, 4-Tier Authority Hierarchy)
  │
  ├─► 12. Forensic Hypothesis Engine (Deterministic multi-evidence hypotheses)
  │
  ├─► 13. Next-Best-Evidence Planner (Ordered action recommendations with justifications)
  │
  ├─► 14. Coverage Governor & Hard Gates (Mandatory lane enforcement & gate triggers)
  │
  └─► 15. Identity Forensic Autopsy (Triage Outcome: LOW RISK / REFER / HIGH RISK / INDETERMINATE)
         └─► SQLite Case Persistence & Export (Printable HTML / JSON)
```

## Evidence Authority & Truth Hierarchy

VEDA-BORDER uses a strict 4-tier truth hierarchy to prevent weak probabilistic signals from diluting hard evidence:

- **Tier 1 (Authoritative / Strong):** Authenticated electronic chip credentials (future), Authorized government intelligence (future).
- **Tier 2 (Deterministic Machine-Readable):** MRZ with validated check digits, deterministic document calendar rules, local prototype watchlist.
- **Tier 3 (Observed Document Evidence):** Visible OCR extraction (VIZ), local image-forensic observations, document portrait region.
- **Tier 4 (Probabilistic / Biometric):** 1:1 Face verification cosine similarity, learned tamper output (future), biometric multi-identity linkage.

*Principle:* Lower numeric tier has strictly higher authority. Multiple Tier-4 PASS signals can never cancel a Tier-2 critical contradiction.

## Forensic Hypotheses Engine

Deterministic, evidence-grounded hypotheses generated per screening:
1. `POSSIBLE_VISIBLE_BIOGRAPHIC_FIELD_ALTERATION` (VIZ vs MRZ mismatch)
2. `POSSIBLE_PORTRAIT_SUBSTITUTION` (Biometric face mismatch)
3. `POSSIBLE_DOCUMENT_REGION_MANIPULATION` (Visual forensic edge/noise anomaly)
4. `POSSIBLE_MULTI_IDENTITY_USAGE` (Same biometric embedding linked to conflicting identities)
5. `DOCUMENT_STATUS_ALERT` (Local watchlist hit or expired document)
6. `INSUFFICIENT_FORENSIC_COVERAGE` (Missing mandatory evidence lanes)
7. `NO_CURRENT_CROSS_SOURCE_CONTRADICTION` (Consistent cross-source evidence)

## Next-Best-Evidence Action Planner

Provides the border officer with prioritized, actionable next steps:
- `RECAPTURE_DOCUMENT` (When image quality fails thresholds)
- `RECAPTURE_FIELD_REGION` (Targeted re-scan of conflicting fields)
- `CAPTURE_HIGHER_RESOLUTION_REGION` (Distinguish OCR noise from forgery)
- `RUN_VISUAL_FORENSICS` (Inspect manipulated regions)
- `CAPTURE_LIVE_FACE` / `RUN_FACE_VERIFICATION` (Biometric confirmation)
- `RETRY_THREAT_INTELLIGENCE` (Watchlist lane recovery)
- `REFER_TO_SECONDARY_INSPECTION` (Hard gate triggered)
- `READ_ELECTRONIC_CREDENTIAL` (Future authenticated chip fallback)

## Screening Triage Outcomes

- **LOW_RISK:** All mandatory lanes completed; no contradictions, alerts, or anomalies.
- **REFER:** Visual forensic anomaly, expired document, or multi-identity linkage detected. Officer review required.
- **HIGH_RISK:** Active hard gate triggered (e.g. Critical VIZ/MRZ mismatch, Blacklist hit, Live biometric mismatch).
- **INDETERMINATE:** Mandatory evidence incomplete, lane execution failed, or capture quality unacceptable.
