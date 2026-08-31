# SIDTD: Synthetic Dataset of ID and Travel Document

## Overview
SIDTD is a public research benchmark developed by the Computer Vision Center (CVC) at Universitat Autònoma de Barcelona in collaboration with TC-11. It provides synthetic identity documents derived from the MIDV-2020 layout templates, containing bonafide (genuine) samples alongside controlled forgery variations (crop & replace, inpainting).

## Purpose for VEDA-BORDER
Serves as the **Primary External Forgery & Tamper Benchmark** to independently evaluate document tamper detection, edge/noise profile anomalies, and layout integrity heuristics.

## Official Source
- Portal: `http://datasets.cvc.uab.es/SIDTD/`
- GitHub: `https://github.com/Oriolrt/SIDTD_Dataset`
- TC-11 Page: `https://tc11.cvc.uab.es/datasets/SIDTD_1`

## Official Partitions
- `split_normal`: Fixed hold-out partition (Train: 2511, Val: 313, Test: 315) across 10 template classes (`alb`, `aze`, `esp`, `est`, `fin`, `grc`, `lva`, `rus`, `srb`, `svk`).
- `split_kfold`: 10-fold cross-validation partition.
- `split_shot`: Few-shot evaluation partition.

## Leakage Prevention
VEDA uses the official `split_normal` test partition. The test set is completely held out and never seen during detector configuration.
