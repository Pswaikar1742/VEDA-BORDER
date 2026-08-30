# VEDA-BORDER

VEDA-BORDER is an evidence-first fictional credential screening demo. Task 04 adds the first genuinely image-driven path: local Tesseract OCR reads rendered PNG/JPEG pixels, MRZ fields and check digits are parsed independently, VIZ and MRZ values are compared deterministically, and a local synthetic intelligence adapter adds explicitly labelled mock evidence.

The demo does not estimate authenticity, forgery, fraud probability, or real passport performance. Visual tamper AI, biometrics, NFC, external VLMs, real intelligence connections, and later-task governor calibration are not implemented. Those lanes remain visibly `UNAVAILABLE`, so current autopsies normally remain `INDETERMINATE` even when the available lanes pass.

## Local requirements

- Python 3.11+
- Tesseract 5 with the English language pack
- Node.js/npm for the UI
- Local fonts used by the deterministic renderer (DejaVu Sans and Noto Sans Mono, with documented fallbacks in the generator)

## Generate and evaluate the fictional image benchmark

```bash
make api-install
make benchmark
make evaluate-task04
make api-test
```

The generated benchmark contains 4 clean PNGs, 16 controlled PNG variants, and 5 small capture-condition variants (4 PNG, 1 JPEG). Runtime receives image bytes only. The evaluator freezes every prediction before loading `manifest.json` ground truth.

Task 03's reported 100% values were controlled extraction metrics for machine-readable JSON containers. They were not evidence of OCR on document images. Task 04 replaces runtime benchmark specimens with rendered image pixels and reports image extraction, MRZ parsing, and consistency-support metrics only.

## Run the demo

Terminal 1:

```bash
make api-run
```

Terminal 2:

```bash
make web-install
make web-run
```

Open `http://localhost:3000`, then upload a fictional specimen from `data/synthetic_benchmark/specimens/`. The API is at `http://localhost:8000`, with `GET /health` and `POST /api/v1/scan`. Only PNG and JPEG uploads enter the Task 04 OCR path.

`MOCK_BORDER_INTELLIGENCE_ENABLED=false` simulates service unavailability. With mandatory intelligence enabled, coverage remains incomplete and the system cannot clear the case. `MOCK_BORDER_INTELLIGENCE` is local DEMO data, not INTERPOL, MHA, SSB, Passport Seva, immigration, or any government system.
