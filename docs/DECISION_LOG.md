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

## D009 — Pixel-only benchmark boundary
Task 03's JSON-container extraction values are historical controlled metrics, not image OCR evidence. Task 04 runtime accepts only decoded PNG/JPEG pixels and receives no benchmark manifest, identity, filename truth, parent, or transformation label.

## D010 — Fictional rendered credential design
Render a clearly branded VEDA synthetic credential rather than imitate any real passport, Aadhaar, visa, national ID, government emblem, seal, national symbol, numbering scheme, or security pattern. Controlled text variants change only the recorded VIZ region and preserve MRZ pixels.

## D011 — Deterministic contradiction policy
VIZ/MRZ name, document-number, and DOB conflicts are `CRITICAL`; nationality, sex, and expiry conflicts are `HIGH`. Missing source values are `UNAVAILABLE`, never PASS. No risk or fraud probability is emitted.

## D012 — Mock intelligence boundary
Use a local `ThreatIntelligenceAdapter` interface with a development-only `MockBorderIntelligenceAdapter` containing synthetic identifiers. Label all results DEMO/MOCK; do not claim or simulate operational connectivity to any real government or international system.
