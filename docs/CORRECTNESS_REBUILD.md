# VEDA-BORDER current implementation boundary

This note is the current runtime truth for the demo workstation.

- The integrated pipeline executes sequentially. The evidence graph is a post-analysis record and does not execute policy.
- MRZ support is TD3-style in the current parser. TD1/TD2, NFC/PKI, liveness/PAD, government or INTERPOL connectors are not implemented.
- Visual/Image Forensics V1 uses deterministic image measures (spatial residuals, Laplacian variance, modified Z-score/MAD, ORB displacement and JPEG residuals). It is a suspicious-region signal, not proof of forgery and not a learned tamper segmentation model.
- Watchlist data and fixtures are local synthetic research data. The UI must call this a local prototype match.
- LOW_RISK means sufficient available evidence produced no configured contradiction. It does not mean genuine, authentic or legally verified.
- INDETERMINATE is returned when mandatory evidence is unavailable or insufficient. Execution completion alone is not evidence sufficiency.
- FastRouter receives sanitized structured evidence only. Policy and deterministic lanes determine the outcome; invalid provider output is marked DEGRADED and cannot override the outcome.
- Reopened cases do not display an unrelated browser upload. Original specimen pixels are not retained unless artifact metadata explicitly says otherwise.

External dataset mode is sample processing/demo only. It must not display unsupported accuracy, authenticity or benchmark claims.
