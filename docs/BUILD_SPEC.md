# VEDA-BORDER BUILD SPEC v1.0

## 1. Identity
**Project:** VEDA-BORDER  
**Expansion:** Verification & Evidence-Driven Autopsy for Border Identity and Document Screening  
**Core engine:** Identity Forensic Autopsy Engine (IFAE)  
**SIH PS:** 26188 — AI-Based Fake Identity & Document Screening System  
**Organization:** Ministry of Home Affairs  
**Department:** Sashastra Seema Bal (SSB), Police II Division  
**Category:** Software  
**Theme:** Blockchain & Cybersecurity

## 2. Problem interpretation
Border screening is not one binary classification task. The PS includes fake documents, altered photos, modified dates, forged stamps, impersonation, multiple identities, expired/blacklisted documents, and throughput. These map to distinct evidence problems:
- extraction,
- deterministic document validation,
- cross-source consistency,
- image tamper localization,
- biometric verification,
- presentation attack/morph checks,
- intelligence/database lookup,
- identity linkage,
- evidence completeness,
- officer-facing explanation.

## 3. Product thesis
VEDA-BORDER does **not** ask one AI model, “Is this document fake?” It creates an Identity Forensic Autopsy by examining independent evidence lanes, preserving their provenance and failure state, and fusing them into an explainable screening outcome.

## 4. Truth hierarchy
Highest assurance first:
1. **Cryptographic / authoritative evidence** — signed electronic credential, trusted database result.
2. **Deterministic structural evidence** — MRZ check digits, expiry/date logic, document format rules.
3. **Cross-source consistency evidence** — VIZ ↔ MRZ ↔ chip/mock-eCredential ↔ database ↔ face.
4. **AI forensic evidence** — visual tamper localization, photo replacement, abnormal regions.
5. **Biometric evidence** — portrait ↔ live/reference face; liveness/morph where implemented.
6. **Contextual/provider evidence** — VLM second opinion or extraction fallback.

AI must not override stronger contradictory deterministic/cryptographic evidence.

## 5. Mandatory evidence states
Every module returns:
- `PASS`
- `FAIL`
- `SUSPICIOUS`
- `UNAVAILABLE`
- `NOT_APPLICABLE`

`UNAVAILABLE` is not PASS.

## 6. Screening outcomes
The governor returns one of:
- `CLEAR`
- `REVIEW`
- `HIGH_RISK`
- `INDETERMINATE`

Rules:
- Critical hard-gate contradictions can force `HIGH_RISK`.
- Missing mandatory evidence can force `INDETERMINATE`.
- `CLEAR` requires all mandatory lanes either PASS or explicitly NOT_APPLICABLE, with no unresolved critical contradiction.
- The system may expose an **uncalibrated screening risk index** for PS compatibility, but the UI must label it as a screening index, not “probability fake”.

## 7. Monday MVP scope
### MUST
- File upload (PNG/JPG/PDF; fictional/synthetic specimens).
- SHA-256 specimen hash.
- Document/template classification for supported synthetic fixture families.
- OCR/structured field extraction.
- MRZ parser and check-digit validator.
- Expiry/date validation.
- VIZ↔MRZ consistency matrix.
- Controlled text/photo tamper detection on fixtures.
- Portrait extraction and face comparison on synthetic/consented fixtures.
- Mock blacklist adapter.
- Evidence coverage calculation.
- Coverage-aware governor.
- Identity Forensic Autopsy JSON + UI.
- Golden demo fixtures: clean, tampered, unavailable-lane.

### SHOULD
- Webcam capture.
- Basic liveness/PAD if reliable in time.
- Duplicate-identity embedding search on a small synthetic gallery.
- Simulated signed electronic credential lane demonstrating trusted-record contradiction.
- Suspicious-region overlay.

### STRETCH
- Real NFC/ePassport reading.
- ICAO PKD production validation.
- Hologram/dynamic security feature verification.
- Morph attack detector.
- Large-scale unseen-layout generalization.
- Real government/INTERPOL connectors.

## 8. FastRouter policy
FastRouter is permitted for development/testing only as a provider adapter.
Good uses:
- VLM second opinion on suspicious regions,
- difficult OCR/extraction fallback,
- document-type assistance,
- natural-language explanation of already verified findings.

Forbidden as sole authority for:
- MRZ checksums,
- expiry/date rules,
- blacklist truth,
- electronic signature validation,
- final fraud/authenticity decision.

The demo must run with `FASTROUTER_ENABLED=false`.

## 9. MVP data policy
- Do not train on real Indian passports collected from people.
- Use fictional synthetic documents and openly licensed/public research datasets where permitted.
- Store dataset source/license/use in `docs/DATASET_LEDGER.md` before incorporating a dataset.
- Never call synthetic perturbations “real fraud”.
- Ground truth must come from logged transformations or external labels, not from the model being evaluated.

## 10. Demo cases
### Case A — Clean
Expected: all mandatory lanes complete, consistency PASS, blacklist clear → `CLEAR`.

### Case B — Tampered DOB/photo
Expected: MRZ or trusted-record contradiction + tamper signal → `HIGH_RISK` or `REVIEW` according to hard-gate policy, with exact evidence shown.

### Case C — Required lane unavailable
Expected: e.g. forensics/biometric provider intentionally disabled → coverage drops and result becomes `INDETERMINATE`, not CLEAR.

### Case D — Blacklisted synthetic document
Expected: mock threat-intelligence hit → hard-gate `HIGH_RISK`.

### Case E — Same face, different synthetic identity
Expected if SHOULD feature completed: duplicate-identity alert → `REVIEW`/`HIGH_RISK` with linked record IDs.

## 11. Success definition for Monday
A live reviewer can upload fixtures and see:
- what was extracted,
- what was checked,
- what evidence supported each result,
- what failed/unavailable,
- cross-source contradictions,
- why the final outcome was produced,
- repeatable golden tests passing locally.

Do not optimize for pretty UI before these behaviors exist.
