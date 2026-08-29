# Architecture v1

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

## Monday proof target
The prototype must prove three golden cases:
- clean fictional credential -> coherent low-risk/clear outcome with full evidence
- controlled tamper -> localized/cross-source contradiction -> refer/high-risk
- mandatory lane unavailable -> INDETERMINATE/manual review, never clean
