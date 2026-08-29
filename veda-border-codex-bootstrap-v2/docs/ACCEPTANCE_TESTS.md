# Monday Acceptance Tests v1

These are release gates. Codex must not change them to make the build pass.

## AT-001 Repository boots
- API starts locally.
- Web starts locally.
- `/health` returns success.
- `pytest` and frontend tests run.

## AT-002 Specimen integrity
Given a fixture upload:
- SHA-256 is returned.
- scan ID is created.
- unsupported file types are rejected.

## AT-003 MRZ valid fixture
Given a clean fictional MRZ fixture:
- fields parse correctly.
- configured check digits pass.
- evidence records are PASS.

## AT-004 MRZ tamper fixture
Given one changed character in a protected MRZ field:
- at least one relevant check digit fails.
- evidence state is FAIL.
- outcome is not CLEAR.

## AT-005 VIZ ↔ MRZ mismatch
Given a fixture where printed DOB differs from MRZ DOB:
- consistency matrix contains `date_of_birth` FAIL.
- critical/review reason references that mismatch.

## AT-006 Expired document
Given expiry before system date:
- deterministic expiry evidence FAIL.
- outcome is not CLEAR.

## AT-007 Controlled tamper
Given a generated fixture with logged DOB/portrait region modification:
- system returns tamper evidence for the changed fixture.
- any heatmap/bbox produced must be tied to the detector result.
- no claim is made that this establishes real-world fraud intent.

## AT-008 Face mismatch
Given a mismatched reference face fixture:
- biometric lane returns FAIL or SUSPICIOUS according to configured threshold.
- outcome is not CLEAR.

## AT-009 Mock blacklist hard gate
Given a synthetic document number present in mock blacklist:
- intelligence lane FAIL/CRITICAL.
- outcome HIGH_RISK.

## AT-010 Provider failure must fail closed
Disable FastRouter or force provider error on a mandatory configured lane:
- that lane returns UNAVAILABLE.
- coverage report lists it.
- if mandatory for the selected policy, outcome is INDETERMINATE.
- it must never become PASS/CLEAR merely because the call failed.

## AT-011 Explanation traceability
Every final `outcome_reason` references evidence IDs present in the report.

## AT-012 Demo reproducibility
A single command runs the golden demo suite and writes JSON reports for clean, tampered, blacklisted, and unavailable cases.
