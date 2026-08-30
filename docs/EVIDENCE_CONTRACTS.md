# Evidence Contracts v1

## Enums

```python
EvidenceState = PASS | FAIL | SUSPICIOUS | UNAVAILABLE | NOT_APPLICABLE
ScreeningOutcome = CLEAR | REVIEW | HIGH_RISK | INDETERMINATE
Severity = INFO | LOW | MEDIUM | HIGH | CRITICAL
```

## EvidenceRecord

```json
{
  "evidence_id": "mrz.check_digit.document_number",
  "lane": "mrz",
  "state": "PASS",
  "severity": "INFO",
  "mandatory": true,
  "title": "MRZ document-number check digit",
  "summary": "Document number check digit is valid.",
  "observed": "P1234567",
  "expected": "valid_check_digit",
  "source": {
    "kind": "derived",
    "artifact_ref": "specimen:sha256:...",
    "region": null
  },
  "method": {
    "type": "deterministic_rule",
    "implementation": "icao9303_check_digit_v1",
    "provider": null,
    "model": null,
    "version": "1.0"
  },
  "confidence": null,
  "latency_ms": 2,
  "error": null
}
```

## CrossSourceField

```json
{
  "field": "date_of_birth",
  "sources": {
    "viz": "1997-04-12",
    "mrz": "1997-04-12",
    "ecredential": "1994-04-12"
  },
  "state": "FAIL",
  "severity": "CRITICAL",
  "reason": "Trusted electronic record conflicts with printed and MRZ DOB."
}
```

## CoverageReport

```json
{
  "mandatory_total": 8,
  "mandatory_completed": 7,
  "coverage_ratio": 0.875,
  "missing_mandatory": ["biometrics.face_verify"],
  "state": "INCOMPLETE"
}
```

## IdentityForensicAutopsy

```json
{
  "scan_id": "...",
  "specimen_sha256": "...",
  "document_type": "FICTIONAL_PASSPORT",
  "extracted_identity": {},
  "evidence": [],
  "consistency_matrix": [],
  "coverage": {},
  "critical_findings": [],
  "screening_risk_index": 0,
  "risk_index_calibrated": false,
  "outcome": "INDETERMINATE",
  "outcome_reasons": [],
  "recommended_action": "MANUAL_REVIEW"
}
```

### Task 04 extension

The API now exposes these top-level evidence sections while preserving the Task 01 coverage and outcome invariants:

```json
{
  "visible_document_data": {"raw_visible_fields": {}, "visible_fields": {}, "field_confidence": {}, "missing_fields": []},
  "mrz_analysis": {"mrz_detected": true, "fields": {}, "checks": {}, "raw_lines": []},
  "document_rules": [],
  "cross_source_consistency": [],
  "threat_intelligence": {"source": "MOCK_BORDER_INTELLIGENCE", "demo_data": true, "status": "PASS", "result": "CLEAR", "lookups": []},
  "evidence_coverage": {},
  "outcome": "INDETERMINATE"
}
```

Cross-source records contain `field`, `source_a`, `value_a`, `source_b`, `value_b`, `status`, `severity`, and `reason`. Missing source values produce `UNAVAILABLE`. Mock intelligence evidence is local synthetic demo evidence, not authoritative border intelligence.

## Governor invariants
1. `UNAVAILABLE` must never be normalized to PASS or zero-risk evidence.
2. A mandatory unavailable lane is visible in `CoverageReport`.
3. A configured critical hard gate cannot be averaged away by unrelated positive evidence.
4. Risk index and outcome are separate fields.
5. Every outcome reason references one or more `evidence_id` values.
