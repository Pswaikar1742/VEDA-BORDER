# Task 04 Completion Report

Task 04 implements the first image-driven VEDA-BORDER path: actual fictional credential images, pixel-only local OCR/MRZ extraction, deterministic VIZ/MRZ comparisons, deterministic document rules, local DEMO mock intelligence, Task 04 autopsy sections, coverage preservation, a minimal UI extension, and frozen-prediction evaluation. Task 05 and later features were not started.

## Scope and evidence boundary

- Accepted base commit: `dcd02332d0f6f6818045e93977c48fa763a1df0e`.
- Task 03's 100% results were machine-readable JSON-container extraction metrics, not document-image OCR results. The historical report is retained at `data/evaluations/task03_container_evaluation.json` with that limitation embedded.
- Task 04 runtime accepts decoded PNG/JPEG pixels only. `LocalOcrAdapter` has no filename, manifest, specimen ID, parent ID, transformation label, sidecar, or generator-value input.
- The evaluator freezes all predictions from image bytes before it loads `manifest.json` ground truth.
- No real identity data, document design, emblem, seal, national symbol, security pattern, operational identifier, provider, or government database is used.

## Rendered benchmark

- 25 images total: 4 clean PNGs, 16 controlled altered PNGs, and 5 capture-condition images (4 PNG, 1 JPEG).
- Controlled classes: `name_substitution`, `birth_date_substitution`, `expiry_date_substitution`, `portrait_region_replacement` (4 of each).
- Capture classes: `mild_rotation`, `mild_perspective`, `mild_blur`, `jpeg_recompression`, `brightness_variation` (1 of each).
- Every controlled/capture record stores parent, affected field/region, original/replacement, bounding box, SHA-256, generation seed, expected contradiction, and detector-independent truth.
- Same-seed regeneration is byte-identical; all 25 specimen IDs and SHA-256 values are unique and verified.
- Text transformations alter only the logged VIZ row; portrait replacements alter only the logged portrait box. MRZ pixels remain unchanged.

## Runtime and contracts

- OCR backend: local Tesseract 5.5.3, English language data, invoked over decoded pixels. Pillow 12.3.0 handles image validation, deterministic rendering, cropping, and capture transformations.
- Visible extraction returns raw OCR text, raw label values, normalized values, field confidence where Tesseract provides it, missing fields, and uncertain fields. Missing values are never filled from truth.
- MRZ extraction returns raw OCR lines, parsed fields, individual check states, and errors. Deterministic parsing tolerates only missing trailing name-line filler characters; it does not consult truth.
- VIZ/MRZ comparisons cover holder name, document number, nationality, DOB, sex, and expiry. Missing values are `UNAVAILABLE`.
- Contradiction policy: name/document/DOB are `CRITICAL`; nationality/sex/expiry are `HIGH`. No probability or arbitrary score exists.
- `ThreatIntelligenceAdapter` and `MockBorderIntelligenceAdapter` support `CLEAR`, `DOCUMENT_BLACKLISTED`, `IDENTITY_WATCHLIST_MATCH`, and `UNAVAILABLE`, using only local synthetic entries. Evidence is labelled `MOCK_BORDER_INTELLIGENCE` and `DEMO`.
- Autopsy sections now include `visible_document_data`, `mrz_analysis`, `document_rules`, `cross_source_consistency`, `threat_intelligence`, `evidence_coverage`, and `outcome`. Visual tamper, biometric, and NFC lanes remain explicit `UNAVAILABLE`.

## Measured image metrics

These are extraction, MRZ parsing, deterministic validation, and consistency-support metrics on a small, controlled synthetic layout. They are not fraud, forgery, authenticity, or real-passport performance metrics.

| Group | Images | VIZ exact | VIZ normalized | MRZ detection | MRZ fields | MRZ check digits | Extraction failures | Consistency status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Clean | 4 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 0.00% | 100.00% |
| Controlled altered | 16 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 0.00% | 100.00% |
| Capture degradation | 5 | 96.67% | 96.67% | 100.00% | 100.00% | 100.00% | 0.00% | 96.67% |
| All | 25 | 99.33% | 99.33% | 100.00% | 100.00% | 100.00% | 0.00% | 99.33% |

All normalized per-field accuracy is 100% except document number at 96% overall (80% in the five-image capture subset). The retained error is `capture-001-04.jpg`: VIZ `VDA111111` was OCRed as `VDAI111111`. All 12 expected text contradictions were detected (100% support-set detection); this is not a tamper/fraud detector metric.

## Golden cases

- A clean consistent: all six VIZ/MRZ comparisons PASS; all five MRZ check digits PASS; mock intelligence `CLEAR`. Autopsy outcome remains `INDETERMINATE` because mandatory visual-tamper and biometric evidence is unavailable.
- B DOB alteration: VIZ `1991-06-18` vs MRZ `1994-03-17` -> `FAIL / CRITICAL`.
- C name alteration: VIZ `LIO MAREN` vs MRZ `ARI SOLEN` -> `FAIL / CRITICAL`.
- D expiry alteration: VIZ `2021-02-21` vs MRZ `2031-02-21` -> `FAIL / HIGH`; deterministic current-expiry rule also fails.
- E synthetic blacklist: `VDA444444` -> intelligence `FAIL / DOCUMENT_BLACKLISTED`, source `MOCK_BORDER_INTELLIGENCE`.
- F intelligence unavailable: disabled mock -> intelligence `UNAVAILABLE`; mandatory coverage is `INCOMPLETE`; outcome `INDETERMINATE`.
- Synthetic identity watchlist behavior is additionally unit-tested with `WATCH DEMO`.

## Verification

- Baseline before changes: `python3 -m pytest -q services/api/tests` -> 17 passed.
- Final backend: `python3 -m pytest -q services/api/tests` -> 26 passed, 1004 third-party deprecation warnings, no failures.
- Frontend dependencies: `npm ci` -> completed from the committed lockfile; npm warned that the pinned Next.js 14.2.5 version has a published security issue.
- Frontend: `npm run build` -> compiled, linted, type-checked, and generated static pages successfully.
- `python3 -m compileall -q services/api/app services/api/tools` -> passed.
- `git diff --check` -> passed.
- Artifact audit -> 25 records, 24 PNG, 1 JPEG, 25 unique hashes; every manifest hash matches its image.
- Generator and evaluator: `python3 services/api/tools/generate_synthetic_benchmark.py` and `python3 services/api/tools/evaluate_task04.py` -> passed; report at `data/synthetic_benchmark/task04_evaluation.json`.

## Files changed

- Runtime: `services/api/app/{benchmark,config,contracts,extraction,mrz,pipeline}.py`, `services/api/app/routes/scan.py`.
- New runtime modules: `services/api/app/consistency.py`, `services/api/app/intelligence.py`.
- Tools: `services/api/tools/generate_synthetic_benchmark.py`, new `services/api/tools/evaluate_task04.py`.
- Tests: `services/api/tests/test_benchmark.py`, `services/api/tests/test_task03.py`, new `services/api/tests/test_task04.py`; Task 01 contract/API tests remain present and passing.
- UI/config: `apps/web/app/page.tsx`, `.env.example`, `Makefile`, `services/api/requirements.txt`.
- Documentation: `README.md`, `docs/ARCHITECTURE.md`, `docs/DATASET_LEDGER.md`, `docs/DECISION_LOG.md`, `docs/EVIDENCE_CONTRACTS.md`, `TASK_REPORT.md`.
- Artifacts: replaced 20 runtime JSON specimens with 25 image specimens; updated manifest; replaced the Task 03 output in the active benchmark directory with `task04_evaluation.json`; retained Task 03 history in `data/evaluations/task03_container_evaluation.json`.

## Failures, limitations, conflicts, and deferred work

- No backend test, build, generator, evaluator, schema, hash, or golden-case failure remains.
- An initial frontend build attempt failed because dependencies were absent (`next: command not found`); after `npm ci`, the build passed.
- A live localhost curl smoke check could not cross the managed sandbox's isolated network namespace even though Uvicorn started successfully. The checked API-route upload test in the 26-test suite covers the PNG request/response path; local demo commands are provided below.
- The measured JPEG VIZ `1`/`I` error is intentionally retained. The proportional crop strategy is designed for the VEDA synthetic layout, not unseen real credentials or arbitrary camera framing.
- PNG/JPEG are supported in Task 04. PDF conversion/extraction remains a broader build-spec target and is intentionally not invented in this pixel benchmark task.
- The npm install warning for pinned Next.js 14.2.5 is a known dependency risk; upgrading the framework was intentionally deferred because it is outside Task 04 and requires its own compatibility/security task.
- No unresolved specification conflict was found. The detailed Task 04 instruction governs current outcomes: unlike the broader eventual clean-case target in `BUILD_SPEC`, missing mandatory later lanes keep Task 04 autopsies `INDETERMINATE`.
- Synthetic benchmark performance does not estimate real passport or camera performance. No calibration exists and no fraud probability is reported.
- Intentionally deferred exactly as required: visual tamper AI/models, FastRouter/VLM calls, biometrics/face/liveness/morph, duplicate identity graph, NFC/ePassport/PKD, real intelligence or blacklist integrations, blockchain, final risk calibration/governor, and Task 05+.

## Exact local demo commands

```bash
make api-install
make benchmark
make evaluate-task04
make api-test
make api-run
```

In a second terminal:

```bash
make web-install
make web-run
```

Open `http://localhost:3000` and upload a file from `data/synthetic_benchmark/specimens/`.
