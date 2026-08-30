# Dataset Ledger

Do not add a dataset without recording its terms.

| Dataset | Purpose | Source | License / Terms | Competition Use OK? | PII / Sensitivity | Split Strategy | Status |
|---|---|---|---|---|---|---|---|
| Synthetic VEDA rendered-image benchmark v2 | Task 04 OCR/MRZ/consistency support and golden cases: 4 clean, 16 controlled visible/portrait variants, 5 capture-condition variants | Deterministically generated in repo | Project-owned | Yes | Entirely fictional; no real PII | Parent-linked transformations; evaluation truth loaded only after frozen byte-only predictions | GENERATED / TASK 04 |
| DLC-2021 metadata/baseline subset | Legitimate external synthetic/mock-document reference | Zenodo record 6466768 | CC BY-SA 2.5; Generated Photos attribution noted in license | Verify for derivatives | Synthetic IDs/artificial personal information | Not used for Task 03 scoring | DOWNLOADED METADATA ONLY |
| FantasyID | ID tamper research | Idiap | Verify at acquisition | Verify | Synthetic/fantasy | template/style-disjoint | CANDIDATE |
| MIDV-2020 | OCR/capture robustness | Public research dataset | Verify at acquisition | Verify | Synthetic/mock IDs | document/template-disjoint | CANDIDATE |
| FRLL-Morphs | Morph evaluation | Public research release | Verify at acquisition | Verify | Face images | subject-disjoint | STRETCH |
| MIDV-Holo | Hologram/security feature | Public research release | Verify at acquisition | Verify | ID-like research data | video/document-disjoint | STRETCH |

Never treat Aegis invoice/health benchmark labels as real border fraud ground truth.

Task 03's JSON-container benchmark results were controlled container-level extraction metrics, not image OCR evidence. Task 04 specimens are actual rendered PNG/JPEG files. Their measured results are specific to this small synthetic layout and do not estimate real passport, visa, national-ID, camera, fraud, forgery, or authenticity performance.
