# Task 01 — Repository Scaffold + Evidence Contracts

## Goal
Create the minimum runnable VEDA-BORDER monorepo foundation. Do not implement OCR, MRZ parsing, tamper detection, face recognition, blacklist logic, or scoring yet.

## Required structure
Create at least:

- `apps/web/` — Next.js + TypeScript officer UI shell
- `services/api/` — FastAPI backend
- `services/api/app/main.py`
- `services/api/app/contracts.py`
- `services/api/app/config.py`
- `services/api/app/routes/health.py`
- `services/api/app/routes/scan.py`
- `services/api/tests/`
- `.env.example`
- `.gitignore`
- root `Makefile` or equivalent developer commands

You may adjust exact internal paths if necessary, but keep the architecture simple and documented.

## Backend acceptance requirements
Implement:
1. `GET /health` returning service readiness.
2. `POST /api/v1/scan` accepting a synthetic/demo file upload and returning a typed placeholder `IdentityForensicAutopsy`.
3. SHA-256 computation over uploaded bytes.
4. Evidence status enum exactly supporting:
   - PASS
   - FAIL
   - SUSPICIOUS
   - UNAVAILABLE
   - NOT_APPLICABLE
5. Decision/outcome enum supporting at least:
   - CLEAR
   - REFER
   - INDETERMINATE
6. Evidence-lane result structure with:
   - lane id/name
   - status
   - summary/reason
   - evidence items / findings
   - required flag
   - provider/source metadata when relevant
7. Top-level autopsy object with:
   - specimen filename
   - SHA-256
   - evidence lanes
   - evidence coverage summary
   - outcome
   - critical findings
   - disclaimer / human-review statement

For Task 01 every detector lane can be a placeholder `UNAVAILABLE`, but the governor semantics must not return CLEAR when a required lane is unavailable. A sample scan should therefore be INDETERMINATE unless explicitly configured otherwise.

## Frontend acceptance requirements
Create a minimal page that:
- shows VEDA-BORDER branding
- can select/upload a file
- calls the scan endpoint
- renders filename/hash
- renders lane status cards
- renders evidence coverage
- renders the overall outcome
- clearly distinguishes UNAVAILABLE from PASS

No visual polish beyond a usable technical demo shell is required.

## Config / provider boundary
Add `.env.example` containing placeholders for:
- `FASTROUTER_API_KEY=`
- `FASTROUTER_BASE_URL=`
- `FASTROUTER_MODEL=`
- `FASTROUTER_ENABLED=false`
- optional spend/request cap setting

No provider call is required in Task 01.

## Tests
Add tests that prove:
- SHA-256 is deterministic for fixed bytes.
- status enum serializes correctly.
- required UNAVAILABLE evidence cannot produce CLEAR.
- health endpoint works.
- scan endpoint returns typed JSON with INDETERMINATE when required placeholder evidence is unavailable.

## Documentation
Update README with local run instructions and briefly document the Task 01 architecture.

## Prohibited in this task
- no fake accuracy claims
- no hard-coded fraud probability
- no blockchain
- no LangGraph/agent mesh unless technically necessary (it should not be)
- no real identity documents in fixtures
- no external API calls
- no Task 02 work
