# Architecture v1.1 — Task 04 image path

## Core pipeline

1. Specimen ingestion + SHA-256
2. Capture/document quality gate
3. Document type/template identification
4. OCR / VIZ extraction
5. MRZ extraction + deterministic checks
6. Date/expiry/format validation
7. Cross-source consistency engine (VIZ <-> MRZ; simulated chip/DB when available)
8. Visual forensics lane (optional provider/local detector)
9. Biometric lane (document portrait vs reference/live face; optional PAD)
10. Intelligence lane (mock blacklist; duplicate identity linkage later)
11. Evidence coverage governor
12. Identity Forensic Autopsy response + officer UI

## Implemented Task 04 flow

```text
fictional PNG/JPEG bytes
  -> local Tesseract OCR over decoded pixels
  -> raw and normalized VIZ fields + confidence/missing fields
  -> independently OCRed fictional MRZ region
  -> MRZ parse + deterministic check digits
  -> deterministic field-by-field VIZ/MRZ comparisons
  -> deterministic dates/expiry rules
  -> local DEMO mock intelligence adapter
  -> evidence lanes + coverage-aware Identity Forensic Autopsy
```

The OCR adapter accepts only decoded PNG/JPEG pixels. It has no filename, specimen ID, parent ID, transformation class, manifest, sidecar, or generator-value input. Benchmark evaluation enumerates image files, freezes all runtime predictions, and only then loads evaluation ground truth.

The rendered fixtures use a deliberately fictional VEDA layout, fictional state code and authority, geometric fictional portraits, synthetic identifiers, and two explicit warnings. They do not reproduce a passport, Aadhaar, visa, national ID, emblem, seal, national symbol, or operational security pattern.

## Cross-source consistency

The consistency engine compares holder name, document number, nationality, DOB, sex, and expiry. Dates are converted to ISO calendar values and textual values use field-specific deterministic normalization. A missing VIZ or MRZ value yields `UNAVAILABLE`, never `PASS`. The configurable contradiction policy assigns `CRITICAL` to name, document-number, and DOB conflicts and `HIGH` to nationality, sex, and expiry conflicts. It emits evidence values and reasons; it emits no probability.

## Threat intelligence boundary

`ThreatIntelligenceAdapter` defines the local interface. `MockBorderIntelligenceAdapter` contains only synthetic development records and returns `CLEAR`, `DOCUMENT_BLACKLISTED`, `IDENTITY_WATCHLIST_MATCH`, or `UNAVAILABLE`. Every lookup is labelled `MOCK_BORDER_INTELLIGENCE`, `DEMO`, and timestamped. There is no operational government or international database connection.

## Autopsy and coverage

Task 04 exposes `visible_document_data`, `mrz_analysis`, `document_rules`, `cross_source_consistency`, `threat_intelligence`, `evidence_coverage`, and `outcome`. Visual tamper, biometric, and NFC/ePassport lanes remain explicit `UNAVAILABLE`; NFC is non-mandatory at this stage, while visual tamper and biometric lanes remain mandatory. Therefore available-lane PASS evidence does not imply authenticity and does not silently produce clearance.

## Evidence hierarchy

Strongest to weakest for MVP decisioning:
- cryptographic/authoritative evidence when available
- deterministic structural/format/checksum evidence
- exact cross-source consistency evidence
- calibrated biometric/forensic model evidence
- provider-assisted descriptive evidence

AI must never override a deterministic hard contradiction merely because a model score is high.

## Mandatory failure semantics
A lane that cannot execute returns `UNAVAILABLE`. If the lane is mandatory for the configured policy, the governor must not clear the case. It returns `INDETERMINATE` or `MANUAL_REVIEW_REQUIRED`.

## Broader proof target (not all implemented in Task 04)
The prototype must prove three golden cases:
- clean fictional credential -> coherent low-risk/clear outcome with full evidence
- controlled tamper -> localized/cross-source contradiction -> refer/high-risk
- mandatory lane unavailable -> INDETERMINATE/manual review, never clean
