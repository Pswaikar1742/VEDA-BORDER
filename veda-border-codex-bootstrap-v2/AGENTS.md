# VEDA-BORDER Codex Instructions

VEDA-BORDER is the implementation name for SIH 2026 PS 26188: AI-Based Fake Identity & Document Screening System.

## Source of truth
Read these before coding:
1. `docs/BUILD_SPEC.md`
2. `docs/ACCEPTANCE_TESTS.md`
3. `docs/EVIDENCE_CONTRACTS.md`
4. `docs/ARCHITECTURE.md`
5. `docs/THREAT_MODEL.md`
6. `docs/DECISION_LOG.md`
7. the current task under `codex/prompts/`

If a requirement conflicts, stop and report the conflict. Do not silently invent behavior.

## Non-negotiable design rules
- The system is an evidence-first forensic screening platform, not a single fake/real classifier.
- Every analysis lane returns one of: PASS, FAIL, SUSPICIOUS, UNAVAILABLE, NOT_APPLICABLE.
- Missing mandatory evidence must never be treated as positive authenticity evidence.
- When required evidence is unavailable, the governor may return INDETERMINATE / MANUAL_REVIEW_REQUIRED.
- Do not claim a risk score is a fraud probability unless calibration exists.
- Deterministic checks must be implemented deterministically: MRZ checks, dates, expiry, exact cross-field comparisons, mock blacklist hits, evidence coverage.
- External AI/VLM providers are optional support tools and must not be required for the core demo to run.
- Never upload real identity documents or PII to third-party APIs in tests. Use fictional/synthetic fixtures only.
- Do not implement blockchain unless a concrete requirement is added later.
- Preserve an explainable evidence trail in the final Identity Forensic Autopsy.

## Engineering rules
- Prefer simple, testable modules over agent sprawl.
- Backend: Python 3.11+, FastAPI, Pydantic v2.
- Frontend: Next.js + TypeScript.
- Use typed contracts shared conceptually across API and UI.
- Add tests with every task.
- Keep provider adapters behind interfaces.
- Put all secrets in environment variables. Never commit credentials.
- After each task, stop and report: files changed, commands run, tests, failures, limitations, and next risks.

## Scope discipline
Execute only the explicitly assigned task. Do not continue to the next prompt unless instructed.
