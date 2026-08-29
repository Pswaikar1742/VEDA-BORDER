# VEDA-BORDER

Task 01 is the deliberately small, runnable foundation: fictional specimen upload, SHA-256 ingestion, typed IdentityForensicAutopsy JSON, explicit unavailable evidence lanes, coverage-aware `INDETERMINATE` semantics, and a technical Next.js shell. OCR, MRZ, tamper, biometric, blacklist, dataset, and provider calls are intentionally not implemented.

## Run locally

```bash
make api-install
make api-test
make api-run              # http://localhost:8000
cd apps/web && npm install && npm run dev  # http://localhost:3000
```

The API exposes `GET /health` and `POST /api/v1/scan`. FastRouter settings live in `.env.example`; no provider call is made in Task 01.

## Task 02 synthetic benchmark

Run `make benchmark` to generate four clean fantasy credentials and sixteen controlled variants under `data/synthetic_benchmark/`. The JSON manifest records transformation-derived ground truth, parent pairing, parameters, hashes, and expected evidence conditions. These are integrity conditions only, not fraud or authenticity labels. No OCR, MRZ, detector, biometric, scoring, or provider work is included.
