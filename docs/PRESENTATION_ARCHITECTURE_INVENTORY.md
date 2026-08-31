# VEDA-BORDER — Presentation Architecture Inventory

**Document Purpose:** Complete, factual module inventory and runtime dataflow specification for the SIH 2026 Presentation Team and Architecture Diagram generation.  
**Build Target:** Internal Round 2026-09-01  
**Architecture Paradigm:** Evidence-First Identity Forensic Autopsy Engine (IFAE)  

---

## 1. End-to-End Runtime Sequence

```
FRONTEND / FRONT-LINE OFFICER
        │
        │ [Document Image Bytes + Selfie Image Bytes]
        ▼
1. INGESTION & VALIDATION (`app/validation.py`)
        │
        ▼
2. CAPTURE QUALITY GATE (`app/quality.py`) ──[FAIL]──► STOP: INDETERMINATE / MANUAL_REVIEW
        │ [PASS]
        ▼
3. DOCUMENT FAMILY CLASSIFIER (`app/document_families.py`)
        │
        ├──────────────────────┬──────────────────────┬──────────────────────┐
        ▼                      ▼                      ▼                      ▼
4. OCR & VIZ EXTRACTION   5. MRZ PARSER         6. VISUAL FORENSICS   7. BIOMETRICS
   (`app/extraction.py`)  (`app/mrz.py`)        (`app/visual_forensics`) (`app/biometrics.py`)
        │                      │                      │                      │
        │ [VIZ Fields]         │ [MRZ Fields/Checks]  │ [Tamper Anomalies]   │ [Face Match Score]
        ▼                      ▼                      ▼                      ▼
8. CROSS-SOURCE CONSISTENCY ENGINE (`app/consistency.py`)
        │
        ├──────────────────────┬──────────────────────┐
        ▼                      ▼                      ▼
9. VALIDITY RULES        10. THREAT INTEL       11. MULTI-IDENTITY LINKAGE
   (`app/pipeline.py`)   (`app/intelligence.py`) (`app/linkage.py`)
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               ▼
12. ADAPTIVE EVIDENCE GRAPH BUILDER (`app/evidence_graph.py`)
        │
        ▼
13. FORENSIC HYPOTHESIS ENGINE (`app/policy.py`)
        │
        ▼
14. NEXT-BEST-EVIDENCE PLANNER (`app/policy.py`)
        │
        ▼
15. COVERAGE GOVERNOR & HARD GATES (`app/policy.py`)
        │
        ▼
16. IDENTITY FORENSIC AUTOPSY ENGINE (`app/autopsy.py`)
        │
        ├──────────────────────┬──────────────────────┐
        ▼                      ▼                      ▼
17. CASE PERSISTENCE     18. AUDIT EXPORT       19. WORKSTATION UI
    (`app/persistence.py`) (`app/reporting.py`)   (`apps/web/`)
        │
        ▼ [Optional Support]
20. FASTROUTER EXPLANATION ADAPTER (`app/fastrouter_client.py`)
```

---

## 2. Comprehensive Module Inventory

| # | Module Name | Source File(s) | Input | Output | Classification | Implemented | Prototype vs Production | Dependencies | Evidence Tier | Failure Semantics |
|---|---|---|---|---|---|---|---|---|---|---|
| **1** | **Specimen Ingestion & Validation** | `services/api/app/validation.py` | Multipart HTTP upload (specimen, optional selfie) | Raw validated bytes, MIME verification | Deterministic | Yes | Production Ready | Python `magic`, standard library | Ingestion | Rejects payload with HTTP 400 |
| **2** | **Capture Quality Gate** | `services/api/app/quality.py` | Raw specimen bytes | `acceptable` (bool), `findings` (blur, brightness, resolution, exposure clipping) | Deterministic | Yes | Research Prototype | OpenCV (`cv2`) Laplacian variance, histogram clipping | **Tier 1 (Prerequisite)** | Stops downstream analysis $ightarrow$ returns `INDETERMINATE` / `MANUAL_REVIEW_REQUIRED` |
| **3** | **Document Family Classifier** | `services/api/app/document_families.py` | Raw OCR text & metadata | `family` (`TRAVEL_DOCUMENT`, `NATIONAL_ID`, `DRIVING_LICENCE`, etc.) | Hybrid (Keyword + Layout) | Yes | Research Prototype | Regex, token frequency | Routing | Defaults to `UNKNOWN` $ightarrow$ applies generic screening policy |
| **4** | **Visible Zone OCR Extractor** | `services/api/app/extraction.py` | Document image bytes | `raw_visible_fields`, `field_confidence`, raw text | AI / Heuristic | Yes | Research Prototype (V1) | Tesseract 5 (`pytesseract`), OpenCV | **Tier 2 / Tier 3** | Sets fields to empty $ightarrow$ triggers missing evidence finding |
| **5** | **Deterministic MRZ Parser** | `services/api/app/mrz.py` | Raw MRZ image crop / text | `detected` (bool), `fields`, `checks` (composite, DOB, expiry, doc number checksums) | Deterministic | Yes | Production Ready | ICAO 9303 7-3-1 weight algorithms | **Tier 1 (Hard Gate)** | Checksum mismatch triggers `HARD_GATE_TRIGGERED` $ightarrow$ `REFER` |
| **6** | **Visual Forensics Lane** | `services/api/app/visual_forensics.py` | Document image bytes | `status` (`PASS`, `SUSPICIOUS`), `anomalies`, `tamper_regions`, `heuristic_scores` | Heuristic (Signal Processing) | Yes | Research Prototype (V1) | OpenCV Laplacian edges, Sobel gradient variance, ELA | **Tier 3 (Heuristic)** | Degradation returns `UNAVAILABLE` without failing pipeline |
| **7** | **Biometric Face Verification** | `services/api/app/biometrics.py` | Document crop + Live selfie bytes | `status` (`PASS`, `SUSPICIOUS`), `similarity_score`, `verified` (bool) | AI (Deep Learning) | Yes | Production Ready | OpenCV `YuNet` (detector) + `SFace` (128d cosine embedder) | **Tier 1 (Hard Gate)** | Match score $< 0.55$ triggers `HARD_GATE_TRIGGERED` $ightarrow$ `REFER` |
| **8** | **Cross-Source Consistency Engine** | `services/api/app/consistency.py` | VIZ extracted fields + MRZ parsed fields | `status` (`PASS`, `SUSPICIOUS`), `mismatches` (DOB, names, dates, doc number) | Deterministic | Yes | Production Ready | Levenshtein distance, date normalizer | **Tier 1 / Tier 2** | Exact field contradiction triggers `REFER` |
| **9** | **Validity & Expiry Rules Engine** | `services/api/app/pipeline.py` | Extracted dates, current UTC timestamp | `status` (`PASS`, `FAIL`), expiry flags | Deterministic | Yes | Production Ready | Standard library datetime | **Tier 2** | Expired document triggers `REFER` |
| **10** | **Threat Intelligence Watchlist** | `services/api/app/intelligence.py` | Document number, Holder name, DOB | `status` (`PASS`, `FAIL`), `hits` (interpol_id, reason, risk_tier) | Deterministic | Yes | Simulated Prototype | Local SQLite / memory watchlist fixture | **Tier 1 (Hard Gate)** | Watchlist hit triggers `HIGH_RISK` / `INTERCEPT` |
| **11** | **Multi-Identity Linkage Ledger** | `services/api/app/linkage.py` | 128d SFace embedding + Holder identity | `status` (`PASS`, `SUSPICIOUS`), `linked_identities` (alias detection) | AI + Deterministic | Yes | Research Prototype | SQLite embedding store + Cosine similarity $\ge 0.50$ | **Tier 2** | Multiple names for same facial biometric triggers `SUSPICIOUS` |
| **12** | **Adaptive Forensic Evidence Graph** | `services/api/app/evidence_graph.py` | All lane outputs and provenance metadata | Hierarchical DAG nodes, edges, tier assignments, coverage map | Deterministic | Yes | Production Ready | Graph data structure, Pydantic v2 | Aggregation | Aggregates all available signals |
| **13** | **Forensic Hypothesis Engine** | `services/api/app/policy.py` | Evidence graph state | `primary_hypothesis`, `supporting_evidence`, `competing_hypotheses` | Deterministic Rule-Based | Yes | Production Ready | Policy evaluator | Reasoning | Formulates explainable hypothesis |
| **14** | **Next-Best-Evidence Planner** | `services/api/app/policy.py` | Missing evidence items, unresolved contradictions | Ranked list of prioritized next investigative actions | Deterministic | Yes | Production Ready | Action ranking policy | Decision Support | Provides actionable steps for officer |
| **15** | **Coverage Governor & Hard Gates** | `services/api/app/policy.py` | Evidence graph coverage, hard gate triggers | `outcome` (`LOW_RISK`, `REFER`, `HIGH_RISK`, `INDETERMINATE`) | Deterministic | Yes | Production Ready | Hard gate logic, coverage thresholds | Policy Engine | Missing mandatory evidence $ightarrow$ `INDETERMINATE` |
| **16** | **Identity Forensic Autopsy Engine** | `services/api/app/autopsy.py` | Screening analysis result | `IdentityForensicAutopsy` contract payload | Deterministic | Yes | Production Ready | Pydantic v2 | Output | Generates auditable final evidence dossier |
| **17** | **Case Database Ledger** | `services/api/app/persistence.py` | Complete autopsy record | `case_id`, persistent SQLite storage | Deterministic | Yes | Production Ready | SQLite3, WAL mode | Storage | Write errors degrade safely |
| **18** | **Audit Report & Export Generator** | `services/api/app/reporting.py` | Stored case record | Formatted text and JSON autopsy export | Deterministic | Yes | Production Ready | Standard library | Reporting | Exports officer-readable audit trail |
| **19** | **Forensic Workstation UI** | `apps/web/` | User interactions, API responses | Reactive forensic workstation interface | Reactive UI | Yes | Production Ready | Next.js 14, Tailwind CSS, Lucide icons | UI | Displays Evidence Graph, Autopsy, and Planner |
| **20** | **FastRouter Support Provider** | `services/api/app/fastrouter_client.py` | Verified evidence text | Plain English officer explanation | External LLM | Yes | Optional Supportive (Disabled by default) | `httpx`, FastRouter API (`/chat/completions`) | **Tier 4 (Supportive)** | Safely returns `UNAVAILABLE` on failure; never alters evidence |

---

## 3. Evidence Tier Architecture

VEDA-BORDER organizes evidence into four distinct hierarchical tiers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TIER 1: HARD GATES (Authoritative & Cryptographic Invariants)               │
│ • MRZ Checksum Contradictions                                               │
│ • Biometric Portrait Match Failures (Score < 0.55)                           │
│ • Threat Intelligence Watchlist Hits                                        │
│ • Capture Quality Rejection (Blur, Low Resolution, Glare)                   │
│ RULE: Hard Gate failure unconditionally overrides all downstream scores.    │
├─────────────────────────────────────────────────────────────────────────────┤
│ TIER 2: DETERMINISTIC CROSS-SOURCE CONSISTENCY                              │
│ • VIZ-to-MRZ Semantic Field Comparisons (DOB, Expiry, Number)               │
│ • Document Expiry Date vs UTC Clock                                         │
│ • Multi-Identity Alias Linkage (Biometric 128d match to alternate identity) │
├─────────────────────────────────────────────────────────────────────────────┤
│ TIER 3: FORENSIC HEURISTICS & ANOMALY SCORES                                │
│ • Local Error Level Analysis (ELA) and Laplacian Edge Variance              │
│ • High-Frequency Noise Discontinuities around Photo & Text Fields           │
├─────────────────────────────────────────────────────────────────────────────┤
│ TIER 4: SUPPORTIVE NATURAL LANGUAGE EXPLANATION (Optional)                  │
│ • FastRouter LLM plain-language officer summaries                           │
│ RULE: Never authenticates, never overrides, strictly supportive.            │
└─────────────────────────────────────────────────────────────────────────────┘
```
