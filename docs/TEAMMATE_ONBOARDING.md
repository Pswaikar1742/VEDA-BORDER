# VEDA-BORDER teammate handoff

This document is the practical starting point for working on VEDA-BORDER. It describes the repository as it exists now, how to run it locally, where the main behavior lives, how to validate a change, and what should be done next.

VEDA-BORDER is a research prototype for SIH 2026 PS 26188. It is an evidence-first document and identity screening workstation, not an autonomous fake/real classifier. The system records independent evidence lanes and produces an explainable Identity Forensic Autopsy for human review.

## Read these first

Read the documents in this order before changing behavior:

1. `docs/BUILD_SPEC.md` — product scope, evidence rules, outcomes, and data policy.
2. `docs/EVIDENCE_CONTRACTS.md` — response shape and governor invariants.
3. `docs/ACCEPTANCE_TESTS.md` — release gates; do not weaken these tests to make a change pass.
4. `docs/ARCHITECTURE.md` — end-to-end lane order and authority hierarchy.
5. `docs/THREAT_MODEL.md` — threats, trust boundaries, and failure modes.
6. `docs/DECISION_LOG.md` — decisions that must remain stable unless explicitly revisited.
7. `docs/CORRECTNESS_REBUILD.md` — current runtime boundaries and known correctness constraints.
8. `docs/LOCAL_DEMO_RUNBOOK.md` — short UI walkthrough.

When documents disagree, stop and resolve the conflict explicitly. Do not silently invent a third behavior. `BUILD_SPEC.md`, `EVIDENCE_CONTRACTS.md`, and the current implementation/tests are the primary references for behavior.

## Repository map

```text
apps/web/                  Next.js 14 + TypeScript officer workstation
services/api/app/          FastAPI application and analysis lanes
services/api/tests/        Python contract, policy, pipeline, and regression tests
apps/web/tests/            Node tests for officer-facing summaries and rendered UI
services/api/tools/        Fixture generators and evaluation CLIs
data/integrated_fixtures/  Fictional controlled demo documents and manifest
data/external_demo/        Small manifest-allowlisted MIDV-2020 demo subset
data/evaluations/          Reproducible evaluation outputs and metrics
data/external/             Dataset manifests, licenses, and split metadata
docs/                      Specifications, runbooks, benchmark notes, and decisions
```

Important entry points:

- `services/api/app/main.py` creates the FastAPI app and routers.
- `services/api/app/routes/workspace.py` handles the current workstation API, persistence, reports, fixtures, and readiness.
- `services/api/app/integrated_pipeline.py` runs the sequential analysis pipeline.
- `services/api/app/extraction.py` performs local OCR/field extraction.
- `services/api/app/mrz.py` parses and validates the supported TD3 MRZ.
- `services/api/app/consistency.py` compares visible fields with MRZ fields.
- `services/api/app/policy.py` builds coverage, hard gates, hypotheses, actions, and the final outcome.
- `services/api/app/contracts.py` converts analysis output into the API autopsy contract.
- `apps/web/app/page.tsx` composes the main screen; `apps/web/components/OfficerWorkspace.tsx` is the officer-facing workflow.
- `apps/web/lib/api.ts` is the browser API client; `apps/web/lib/types.ts` is the TypeScript contract surface.

## Local setup

Prerequisites:

- Python 3.11 or newer.
- Node.js 18 or newer and npm.
- Tesseract 5 with the English language pack.
- `libgl1` and `libglib2.0-0` on Linux for OpenCV.
- `pdftoppm` if PDF uploads are to be exercised.

On Ubuntu/Debian, the system packages are typically:

```bash
sudo apt-get install tesseract-ocr tesseract-ocr-eng libgl1 libglib2.0-0 poppler-utils
```

Install project dependencies from the repository root:

```bash
make api-install
make web-install
```

For a safe local run, keep the optional provider disabled. Create a local `.env` if needed; `.env` is ignored by Git and must never be committed:

```dotenv
FASTROUTER_ENABLED=false
MOCK_BORDER_INTELLIGENCE_ENABLED=true
THREAT_INTELLIGENCE_MANDATORY=true
VISUAL_FORENSICS_ENABLED=true
BIOMETRICS_ENABLED=true
```

FastRouter is optional support only. The core deterministic pipeline must work without an API key or external provider. Never put a provider key in `NEXT_PUBLIC_*` variables or source files.

## Start and use the application

Terminal 1 — backend:

```bash
make api-run
```

Terminal 2 — frontend:

```bash
make web-run
```

Open `http://localhost:3000`. API Swagger is at `http://localhost:8000/docs`.

Useful read-only checks:

```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/api/v1/system/status
curl -s http://localhost:8000/api/v1/fixtures
```

The current workstation endpoints are:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/screenings` | Upload PNG/JPG/PDF and optional selfie; run and persist a case |
| `GET` | `/api/v1/cases` | List saved cases and summary |
| `GET` | `/api/v1/cases/{case_id}` | Reopen one autopsy |
| `GET` | `/api/v1/cases/{case_id}/report.json` | Download JSON autopsy |
| `GET` | `/api/v1/cases/{case_id}/report.html` | Render printable HTML autopsy |
| `GET` | `/api/v1/identity-linkage` | Show local prototype linkage clusters |
| `GET` | `/api/v1/system/status` | Module readiness/status |
| `GET` | `/api/v1/fixtures` | List manifest-allowlisted integrated fixtures |
| `GET` | `/api/v1/fixtures/{filename}` | Serve an allowlisted fixture image |
| `GET` | `/health` | Basic API health |

Docker is also available:

```bash
docker compose up --build
```

This starts the API on port 8000 and web app on port 3000 by default. Use `API_PORT`, `WEB_PORT`, and `NEXT_PUBLIC_API_URL` for local port changes. The compose file mounts external data read-only and stores the SQLite case database in a named volume.

## What happens during a screening

The integrated pipeline is sequential. It does not use the evidence graph to execute the policy; the graph is a post-analysis explanation of produced evidence.

1. Decode the upload. PNG/JPG are read directly; the first page of a PDF is rendered locally.
2. Apply the capture-quality gate. An unacceptable image stops downstream analysis and produces `INDETERMINATE`-style insufficient evidence.
3. Extract visible fields and raw MRZ text locally.
4. Classify the document family, or use the officer's explicit family selection.
5. Parse a TD3-style MRZ where applicable and run deterministic ICAO 7-3-1 checks.
6. Apply deterministic document rules such as date validity and expiry.
7. Compare VIZ and MRZ fields. Critical identity conflicts must remain visible and cannot be averaged away.
8. Run local visual-forensics measures, optional local face verification, local synthetic watchlist lookup, and local identity-linkage lookup.
9. Build evidence coverage, hard gates, hypotheses, next-best actions, and the evidence graph.
10. Convert the analysis to the typed autopsy contract and persist it in SQLite.
11. The UI renders an officer summary first and exposes technical lane payloads in Developer Mode.

Every lane uses only these evidence states:

`PASS`, `FAIL`, `SUSPICIOUS`, `UNAVAILABLE`, `NOT_APPLICABLE`

`UNAVAILABLE` is never a positive authenticity signal. The screening outcome is policy-driven and must be interpreted as decision support:

`LOW_RISK`, `REFER`, `HIGH_RISK`, or `INDETERMINATE`

Some older notes use `CLEAR`, `REVIEW`, or `MANUAL_REVIEW_REQUIRED`. When updating code or docs, follow the current contract and tests rather than copying those legacy labels.

## Demo fixtures

Use only fictional or explicitly permitted research data during development and demos. The controlled fixtures are under `data/integrated_fixtures/`:

| Fixture | Purpose |
|---|---|
| `travel_clean.png` | Clean travel-document baseline |
| `travel_dob_altered.png` | Controlled visible DOB alteration / VIZ-MRZ contradiction |
| `travel_portrait_replaced.png` | Controlled portrait mismatch |
| `travel_poor_capture.png` | Quality-gate and insufficient-evidence case |
| `travel_expired.png` | Deterministic expiry failure/review case |
| `travel_blacklisted.png` | Synthetic local watchlist hit |
| `national_id.png`, `driving_licence.png`, `visa_or_permit.png` | Non-MRZ family behavior |
| `ari_selfie.png`, `ari_selfie_variant.png`, `lio_selfie.png` | Synthetic/controlled biometric fixtures |

The optional MIDV-2020 sample paths under `data/external_demo/` are intentionally excluded from Git because they are large. See `data/external_demo/MIDV2020/README.md` for local placement. They are sample-processing inputs, not proof of authenticity, fraud detection accuracy, or production OCR performance. Check `docs/DATASET_LEDGER.md` and the dataset-specific notes before adding data.

## Validation commands

Run these before handing off a backend or policy change:

```bash
make api-test
python3 -m pytest -q services/api/tests
```

Run the frontend unit/render checks and production build:

```bash
npm --prefix apps/web test
make web-build
```

Run the integrated controlled evaluation when changing the pipeline, policy, or fixtures:

```bash
make evaluate-integrated
```

Useful scoped evaluators include `make evaluate-task03`, `make evaluate-task04`, and `make evaluate-external`. Treat their generated metrics as evidence for the exact fixture/dataset boundary only. Do not generalize controlled benchmark results into real-world fraud or authenticity claims.

Before committing:

```bash
git diff --check
git status --short
git diff --cached --stat
```

## Current limitations and safety boundaries

- MRZ parsing is TD3-style; TD1/TD2, NFC, PKI, ICAO PKD, and real government/INTERPOL connectors are not implemented.
- The watchlist is a local synthetic mock and must be labeled `LOCAL PROTOTYPE WATCHLIST` or `DEMO/MOCK`.
- Visual forensics uses deterministic local image measures. It is a suspicious-region cue, not proof of forgery and not a learned general tamper detector.
- The biometric threshold is prototype policy for controlled synthetic fixtures, not population calibration.
- Identity linkage is local SQLite embedding search, not an operational identity database.
- FastRouter output is advisory and sanitized. It must not determine MRZ checks, deterministic rules, watchlist truth, or the final outcome.
- `LOW_RISK` means the configured completed lanes found no contradiction; it does not mean genuine, authentic, or legally verified.
- Original specimen pixels are not automatically retained for reopened cases; the UI must say when an image preview is unavailable.
- Never upload real identity documents or PII to third-party APIs. Use fictional/synthetic fixtures only.
- Do not add blockchain, live government connectors, production biometric claims, or unrelated features without a concrete approved requirement.

## Recommended next work

Work in this order and keep each change small enough to validate independently:

1. **Reconcile contracts and docs.** Audit remaining legacy `CLEAR`/`REVIEW`/`LOW_RISK` terminology and make the API, UI, tests, and documentation use one agreed vocabulary.
2. **Run the complete local baseline.** Capture the actual Python test count, frontend test result, integrated evaluation output, web build result, and `/api/v1/system/status` response in a dated validation note.
3. **Strengthen acceptance coverage.** Add endpoint-level tests for PDF conversion, upload-size/type rejection, persistence/reopen behavior, report export, fixture allowlisting, and provider failure closed behavior.
4. **Improve extraction conservatively.** Add field-level fixtures and regression tests for OCR uncertainty. Missing or ambiguous values must remain `UNAVAILABLE`, never guessed as a clean value.
5. **Separate experimental benchmark work.** Keep MIDV/SIDTD/FantasyID/DLC evaluation scripts and metrics clearly separated from runtime demo behavior, with provenance and no truth leakage.
6. **Calibrate only with approved data.** Any biometric threshold, visual-forensics threshold, or risk band change needs documented data, split policy, error analysis, and an update to the decision log.
7. **Only then consider stretch items.** NFC/PKI, liveness/PAD, broader document layouts, and authoritative connectors require new concrete requirements, threat-model review, and new evidence contracts.

For every task, define the exact scope first. Do not start the next item automatically after finishing one.

## Contribution checklist

Before opening a handoff or pull request, record:

- Files changed and why.
- Commands run and their results.
- Tests that passed, failed, or were not run.
- Fixture/dataset boundary used for validation.
- Any known limitations or unresolved risks.
- Confirmation that no secrets, real identity documents, raw PII, or unreviewed external data were added.

The expected development boundary is local and reproducible. A healthy process, configured provider, or generated report is not by itself proof that the requested real behavior works; verify the actual endpoint, UI flow, saved artifact, or evaluation result relevant to the change.
