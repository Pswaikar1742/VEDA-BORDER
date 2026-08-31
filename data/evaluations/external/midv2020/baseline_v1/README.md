# MIDV-2020 External OCR Baseline V1

- **Evaluated At:** 2026-08-31T07:36:49.189255+00:00
- **Total Samples Evaluated:** 4000 across 4 modalities (1,000 unique document identities)
- **Field Exact Match Rate:** 0.00%
- **Field Normalized Match Rate:** 0.00%
- **Substring OCR Match Rate:** 50.71%
- **Mean Character Error Rate (CER):** 93.33%
- **Capture Quality Pass Rate:** 46.35%
- **MRZ Detection Rate (Passports):** 7.81%

## Scientific Invariants
This frozen baseline evaluates VEDA-BORDER un-tuned V1 OCR, MRZ, and quality-gate heuristics over raw pixel inputs.
Predictions were frozen before comparing against ground-truth VIA annotations.
