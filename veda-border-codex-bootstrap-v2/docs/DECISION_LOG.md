# Decision Log

## D001 — Product name
VEDA-BORDER: Verification & Evidence-Driven Autopsy for Border Identity and Document Screening.

## D002 — Core engine
Identity Forensic Autopsy Engine (IFAE).

## D003 — Not a wrapper
No single LLM/VLM fake-vs-real decision. Independent evidence lanes + cross-source consistency + coverage-aware governor.

## D004 — Missing evidence
Mandatory missing evidence => INDETERMINATE / manual review, never positive evidence.

## D005 — Score semantics
Risk band/score is a decision-support summary, not a calibrated fraud probability unless calibration is later demonstrated.

## D006 — FastRouter
Allowed only behind optional provider adapters for supportive tasks. Core deterministic demo must work with FastRouter disabled.

## D007 — Monday MVP scope
Focus on upload, typed evidence contract, OCR/MRZ/rules, cross-source mismatch, controlled tamper evidence, portrait comparison, mock blacklist, coverage governor, officer autopsy UI.

## D008 — Stretch scope
Real ePassport NFC/PKI, hologram video, morph detector, authoritative government connectors, full duplicate-identity graph, production biometric calibration.
