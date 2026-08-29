# Task 03 Completion Report

Task 03 implemented local document extraction, fictional two-line MRZ parsing, deterministic document validation, post-prediction benchmark evaluation, and a minimal UI extension. Task 01 and Task 02 functionality/tests were preserved.

## Scope and safety

The expected Task 03 prompt was missing, so this user specification was authoritative. The benchmark contains fantasy JSON credentials, no real PII, no real identity-document layout, no government marks, and no operational identifier scheme.

## Dataset

- 4 clean specimens.
- 16 controlled variants: 4 variants per clean parent.
- 20 total specimens with one manifest and one canonical JSON artifact per specimen; every variant preserves the original MRZ while changing only its visible field/region.
- Transformations: `name_substitution`, `birth_date_substitution`, `expiry_date_substitution`, and `portrait_region_replacement`.
- Every variant records its parent, field/region, pre/post values, deterministic parameters, file size/hash, and expected condition.
- Ground truth is generated from the transformation log and does not contain detector predictions.

## OCR and MRZ

- Tesseract CLI is used for raster uploads because it is installed locally and requires no external provider. JSON benchmark containers use visible text through the same byte-only adapter.
- MRZ uses 44-character, two-line, TD3-shaped fictional records with document type `X`, fictional state/nationality `NSL`, filler characters, 7-3-1 check digits, optional-data check, composite check, and a 1939/2000 date pivot.
- Rules cover required fields, date parsing, expiry/current validity, expiry-after-DOB, future DOB, malformed/missing MRZ, and individual MRZ checks.

## Results

Evaluation predicted from specimen bytes before loading the manifest: OCR exact-match 1.0, normalized field accuracy 1.0, MRZ field accuracy 1.0, MRZ check-digit validation accuracy 1.0, extraction failure rate 0.0, and no per-field failures. These are controlled extraction metrics, not fraud, forgery, or authenticity accuracy.

## Verification

- `python3 -m pytest -q services/api/tests` — 16 passed after adding Task 03 tests.
- Generator regeneration with a fixed seed produced byte-identical specimen files and manifests.
- Schema, pairings, uniqueness, hashes, provenance, authorized transformations, and detector-independent truth are tested.
- `npm run build` in `apps/web/` — passed; Task 01 frontend remains buildable.
- `python3 services/api/tools/evaluate_task03.py` — produced `data/synthetic_benchmark/task03_evaluation.json`.

## External dataset

The official DLC-2021 Zenodo metadata, license, and small experimental baseline subset are under `data/external/dlc-2021/`; the full 15.0 GiB corpus is not committed and is not used as Task 03 ground truth.

## Limitations and deferred

JSON specimens are controlled machine-readable containers, not camera images; no broad OCR claim is made. FastRouter, VLM, tamper detector, biometrics, scoring, blacklist, identity linkage, NFC, and Task 04+ remain deferred.
