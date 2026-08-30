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

## D013 — Biometric 1:1 Face Verification Architecture
Use pinned local OpenCV models (YuNet detector `face_detection_yunet_2023mar.onnx` and SFace recognizer `face_recognition_sface_2021dec.onnx`) with cosine similarity. Configured prototype threshold is `0.55`, scoped strictly to separate synthetic fixtures; it is explicitly documented as prototype policy, not population calibration.

## D014 — Local Image Visual Forensics
Implement deterministic local noise and edge residual heuristics (`VEDA_LOCAL_IMAGE_FORENSICS`) rather than uncalibrated external tamper models. Explicitly flag findings as layout-specific cues without claiming general passport tamper detection.

## D015 — Multi-Identity Biometric Linkage
Store local 128-dimensional biometric embeddings in a local SQLite store (`LocalIdentityLinkageStore`). Trigger `POSSIBLE_MULTI_IDENTITY_LINKAGE` / `SUSPICIOUS` when cosine similarity >= 0.50 with conflicting claimed identity data (different name or document number).

## D016 — 4-Tier Authority Hierarchy
Structure evidence in a strict 4-tier hierarchy (Tier 1: Chip/Govt; Tier 2: MRZ/Rules/Watchlist; Tier 3: VIZ/Forensics/Portrait; Tier 4: Biometrics/Linkage). Prohibit score averaging that allows multiple weak PASS signals to cancel a critical Tier-2 contradiction.

## D017 — Next-Best-Evidence Action Planner
Accompany every screening with policy-driven, prioritized verification actions (`RECAPTURE_DOCUMENT`, `RECAPTURE_FIELD_REGION`, `CAPTURE_LIVE_FACE`, `REFER_TO_SECONDARY_INSPECTION`, etc.) containing explicit explanations of WHY each action is recommended.

## D018 — Extensible Document Families
Support `TRAVEL_DOCUMENT`, `VISA_OR_PERMIT`, `NATIONAL_ID`, and `DRIVING_LICENCE`. Non-MRZ families evaluate MRZ validation as `NOT_APPLICABLE` (never `PASS` or `FAIL`), ensuring global extensibility.
