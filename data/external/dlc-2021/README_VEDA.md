# Document Liveness Challenge 2021 (DLC-2021)

## Overview
DLC-2021 is an open benchmark for document presentation attack detection (PAD) published in the *Journal of Imaging* (2022) by Smart Engines researchers. It evaluates the physical authenticity of identity documents across 4 presentation modalities:
1. `or`: Original laminated mock IDs (Bona-fide)
2. `cg`: Grayscale unlaminated paper copies (Presentation Attack)
3. `cc`: Color unlaminated paper copies (Presentation Attack)
4. `re`: Screen recaptures from monitors and mobile displays (Presentation Attack)

## Purpose for VEDA-BORDER
Serves as the **Physical Document Presentation Attack (Liveness) Benchmark** to establish baseline capabilities for distinguishing printed paper copies and screen replays from genuine physical credentials.

## Official Source
- Zenodo Records: Part 1 (`7467028`), Part 2 (`7467004`), Part 3 (`7467000`)
- Paper DOI: `10.3390/jimaging8070181`
- Licence: CC-BY-SA-2.5

## Size & Packaging Boundary
The complete uncompressed raw video corpus exceeds 99 GB across 4 split multi-part archives. As per download size policy, VEDA integrates the official lightweight metadata (`dlc-2021.csv`, 1,424 records), official split lists, and experimental baseline models (`experimental_baseline.zip`, 84.3 MB).
