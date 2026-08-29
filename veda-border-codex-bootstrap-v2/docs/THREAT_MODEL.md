# Threat Model v1

## Threats explicitly mapped from PS 26188
- fake passport / visa / national ID
- altered photograph
- modified date of birth / name / expiry / document number
- tampered visa/stamp region
- identity impersonation
- multiple identities used by the same person
- expired document
- blacklisted/revoked/lost/stolen document (mock adapter in MVP)
- high passenger volume / time pressure

## Additional system threats
- poor capture quality causing false forensic signals
- OCR error causing wrong deterministic validation
- provider outage or invalid API credential
- provider hallucination / unsupported explanation
- prompt injection through OCR/document text
- replay/photo attack against face capture
- score misuse as a probability of fraud
- missing evidence being interpreted as clean
- sensitive PII leakage to logs or third-party services

## Trust boundary
The system is decision support for border officers. It does not autonomously make legal detention/admission decisions.
