# External Standardized Datasets & Benchmark Integration

This document defines the standardized external benchmarks integrated into VEDA-BORDER to independently evaluate optical character recognition, document manipulation detection, visual forensics, presentation attack detection (liveness), and capture robustness.

---

## 1. Primary External Forgery Benchmark: SIDTD

- **Dataset Identifier:** `SIDTD` (Synthetic Dataset of ID and Travel Document)
- **Official Publisher / Source:** TC-11 / Computer Vision Center (CVC), Universitat Autònoma de Barcelona
- **Official Repository:** [https://github.com/Oriolrt/SIDTD_Dataset](https://github.com/Oriolrt/SIDTD_Dataset)
- **Official Portal:** [http://datasets.cvc.uab.es/SIDTD/](http://datasets.cvc.uab.es/SIDTD/)
- **Licence:** Open Research / MIT (Code) & CVC Dataset Terms
- **Access Status:** `DOWNLOADED` / `AVAILABLE`
- **Supported Capabilities:** Document Forgery Detection, Tamper Localization, Layout Manipulation
- **Official Split Strategy:** `split_normal` (Train: 2,511, Val: 313, Test: 315) across 10 template classes (`alb`, `aze`, `esp`, `est`, `fin`, `grc`, `lva`, `rus`, `srb`, `svk`).
- **VEDA Subset:** Static template images (clean bonafide derived from MIDV-2020 + controlled crop-and-replace & inpainting forgeries).
- **Leakage Controls:** Official predefined splits partition templates with template-level grouping; test instances are held out and never seen during configuration.
- **Citation:**
  > O. Ramos Terrades et al., "SIDTD: Synthetic Identity Document Tampering Dataset," Computer Vision Center & TC-11, 2023.

---

## 2. Digital Manipulation Benchmark: FantasyID

- **Dataset Identifier:** `FantasyID`
- **Official Publisher / Source:** Idiap Research Institute, Switzerland
- **Zenodo DOI:** [10.34777/c966-nn94](https://zenodo.org/records/17063366) / Record 17063366
- **Licence:** Creative Commons Attribution 4.0 International (`CC-BY-4.0`)
- **Access Status:** `DOWNLOADED` / `AVAILABLE`
- **Supported Capabilities:** Digital ID Forgery Detection, Face Swapping, Inpainted Text Replacement across 13 Language Templates (including Hindi `hin`, French `fra`, Arabic `ara`, Russian `rus`, Chinese `chi`, English `eng`, etc.).
- **VEDA Subset:** Held-out validation and test partitions across represented language groups.
- **Leakage Controls:** Template and language-style disjoint partitions; evaluation occurs strictly after predictions are frozen.
- **Citation:**
  > Idiap Research Institute, "FantasyID: A Multi-Language Dataset of Synthetic ID Documents for Digital Manipulation Detection," ICCV 2025 DeepID Challenge, 2025.

---

## 3. Physical Document Presentation Attack (Liveness): DLC-2021

- **Dataset Identifier:** `DLC-2021` (Document Liveness Challenge 2021)
- **Official Publisher / Source:** Smart Engines / Journal of Imaging (MDPI) / Zenodo
- **Zenodo DOI:** [10.5281/zenodo.7467028](https://doi.org/10.5281/zenodo.7467028)
- **Paper DOI:** [10.3390/jimaging8070181](https://doi.org/10.3390/jimaging8070181)
- **Licence:** Creative Commons Attribution-ShareAlike 2.5 (`CC-BY-SA-2.5`)
- **Access Status:** `METADATA_AND_BASELINE_DOWNLOADED` (Full 99 GB raw video archives documented; lightweight official metadata and experimental baseline integrated).
- **Supported Capabilities:** Physical Presentation Attack Detection (Original Mock `or` vs Grayscale Copy `cg` vs Color Copy `cc` vs Screen Recapture `re`).
- **Official Split Lists:** `graycopy_test.lst`, `screen_test.lst`, `unlaminated_test.lst`.
- **Leakage Controls:** Document template grouping (`alb_id/00`, `rus_passport/01`, etc.) prevents frames from the same physical document appearing in both train and test partitions.
- **Citation:**
  > D. Polevoy et al., "Document Liveness Challenge Dataset (DLC-2021)," *Journal of Imaging*, vol. 8, no. 7, p. 181, 2022.

---

## 4. Document Localization & OCR Robustness: MIDV-2020

- **Dataset Identifier:** `MIDV-2020`
- **Official Publisher / Source:** L3i Laboratory, La Rochelle University (France) & Smart Engines
- **Access Status:** `DOWNLOADED` / `AVAILABLE` (Official SFTP Access Approved)
- **Official Distribution Server:** `l3i-share.univ-lr.fr` (SFTP Server)
- **Licence:** Creative Commons Attribution-ShareAlike 2.5 Generic (`CC-BY-SA-2.5`)
- **Integrated Modalities:**
  - `templates/`: 1,000 canonical digital template renderings + 10 VIA JSON annotation schemas.
  - `scan_upright/`: 1,000 flatbed scanner captures (upright) + 10 VIA JSON annotation schemas.
  - `scan_rotated/`: 1,000 flatbed scanner captures (rotated) + 10 VIA JSON annotation schemas.
  - `photo/`: 1,000 smartphone captures (Samsung S10 & iPhone XR) across 8 capturing conditions (glare, low light, clutter, perspective distortion) + 10 VIA JSON annotation schemas.
- **Supported Capabilities:** Camera perspective, illumination variations, field boundary localization, and OCR field extraction accuracy under realistic conditions across 10 international document types.
- **Leakage Controls:** Template-level and document-level disjoint partitioning.
- **Citation:**
  > V. V. Arlazarov, K. Bulatov, T. Chernov et al., "MIDV-2020: A Comprehensive Benchmark Dataset for Identity Documents Analysis," Computer Vision and Pattern Recognition, 2021.

---

## 5. Security Feature & Hologram Research: MIDV-Holo

- **Dataset Identifier:** `MIDV-Holo`
- **Official Publisher / Source:** Smart Engines / ResearchGate
- **Access Status:** `DEFERRED` (Metadata registered for future dynamic optical variable device evaluation).

---

## 6. International Standards & Reference Specifications (Not Training Datasets)

- **ICAO Doc 9303 (Parts 1–12):** Machine Readable Travel Documents (MRTDs), specifications for TD1/TD2/TD3 sizes, check digits (7-3-1 weighting), optical character recognition, and electronic chip access (BAC, SAC/PACE, Active Authentication).
- **BSI TR-03105:** Conformity Testing for eMRTD and Chip Inspection Systems (Federal Office for Information Security, Germany).
