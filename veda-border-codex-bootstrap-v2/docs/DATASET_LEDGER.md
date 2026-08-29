# Dataset Ledger

Do not add a dataset without recording its terms.

| Dataset | Purpose | Source | License / Terms | Competition Use OK? | PII / Sensitivity | Split Strategy | Status |
|---|---|---|---|---|---|---|---|
| Synthetic VEDA fixtures | Golden MVP tests | Generated in repo | Project-owned | Yes | None | fixture-level + template-disjoint where possible | REQUIRED |
| FantasyID | ID tamper research | Idiap | Verify at acquisition | Verify | Synthetic/fantasy | template/style-disjoint | CANDIDATE |
| MIDV-2020 | OCR/capture robustness | Public research dataset | Verify at acquisition | Verify | Synthetic/mock IDs | document/template-disjoint | CANDIDATE |
| FRLL-Morphs | Morph evaluation | Public research release | Verify at acquisition | Verify | Face images | subject-disjoint | STRETCH |
| MIDV-Holo | Hologram/security feature | Public research release | Verify at acquisition | Verify | ID-like research data | video/document-disjoint | STRETCH |

Never treat Aegis invoice/health benchmark labels as real border fraud ground truth.
