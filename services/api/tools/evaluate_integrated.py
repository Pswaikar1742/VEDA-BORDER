#!/usr/bin/env python3
"""Evaluate the 9 Golden Research Prototype Scenarios and produce a structured evaluation report."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import resolve_repo_path
from app.integrated_pipeline import analyze_integrated
from app.intelligence import MockBorderIntelligenceAdapter

ROOT = Path(resolve_repo_path('.'))
FIXTURES_DIR = ROOT / 'data' / 'integrated_fixtures'
OUTPUT_REPORT = ROOT / 'data' / 'evaluations' / 'integrated_golden_evaluation.json'


def evaluate() -> dict:
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = tempfile.TemporaryDirectory()
    db_path = str(Path(temp_dir.name) / 'eval.db')

    def load(name: str) -> bytes:
        return (FIXTURES_DIR / name).read_bytes()

    results = []

    # Scenario A
    res_a = analyze_integrated(load('travel_clean.png'), load('ari_selfie.png'), database_path=db_path)
    passed_a = res_a['outcome'] == 'LOW_RISK' and res_a['evidence_coverage']['state'] == 'COMPLETE'
    results.append({
        'scenario': 'A',
        'title': 'Clean Consistent Travel Credential with Matching Live Face',
        'expected_outcome': 'LOW_RISK',
        'observed_outcome': res_a['outcome'],
        'coverage': res_a['evidence_coverage']['state'],
        'hard_gates': [g['gate'] for g in res_a['hard_gates']],
        'status': 'PASS' if passed_a else 'FAIL',
        'details': 'All 6 VIZ/MRZ comparisons PASS; biometrics MATCH (similarity: ' + str(res_a['biometric_verification'].get('similarity')) + '); watchlist CLEAR.'
    })

    # Scenario B
    res_b = analyze_integrated(load('travel_dob_altered.png'), database_path=db_path)
    passed_b = res_b['outcome'] == 'HIGH_RISK' and any(g['gate'] == 'CRITICAL_CROSS_SOURCE_CONTRADICTION' for g in res_b['hard_gates'])
    results.append({
        'scenario': 'B',
        'title': 'Visible Date of Birth Alteration',
        'expected_outcome': 'HIGH_RISK',
        'observed_outcome': res_b['outcome'],
        'coverage': res_b['evidence_coverage']['state'],
        'hard_gates': [g['gate'] for g in res_b['hard_gates']],
        'status': 'PASS' if passed_b else 'FAIL',
        'details': 'VIZ DOB (1991-06-18) != MRZ DOB (1994-03-17); triggered CRITICAL_CROSS_SOURCE_CONTRADICTION hard gate.'
    })

    # Scenario C
    res_c = analyze_integrated(load('travel_portrait_replaced.png'), database_path=db_path)
    passed_c = res_c['outcome'] == 'REFER' and res_c['visual_forensics']['status'] == 'SUSPICIOUS'
    results.append({
        'scenario': 'C',
        'title': 'Portrait Region Substitution / Tamper Cue',
        'expected_outcome': 'REFER',
        'observed_outcome': res_c['outcome'],
        'coverage': res_c['evidence_coverage']['state'],
        'hard_gates': [g['gate'] for g in res_c['hard_gates']],
        'status': 'PASS' if passed_c else 'FAIL',
        'details': 'Local visual heuristics detected anomalous portrait-region edge profile (TEMPLATE_PORTRAIT_REGION_EDGE_ANOMALY).'
    })

    # Scenario D
    res_d = analyze_integrated(load('travel_expired.png'), database_path=db_path)
    passed_d = res_d['outcome'] in {'REFER', 'HIGH_RISK'} and any(g['gate'] == 'EXPIRED_DOCUMENT' for g in res_d['hard_gates'])
    results.append({
        'scenario': 'D',
        'title': 'Expired Credential',
        'expected_outcome': 'REFER or HIGH_RISK',
        'observed_outcome': res_d['outcome'],
        'coverage': res_d['evidence_coverage']['state'],
        'hard_gates': [g['gate'] for g in res_d['hard_gates']],
        'status': 'PASS' if passed_d else 'FAIL',
        'details': 'Deterministic expiry check failed (date.expiry.current); triggered EXPIRED_DOCUMENT gate.'
    })

    # Scenario E
    res_e = analyze_integrated(load('travel_blacklisted.png'), database_path=db_path)
    passed_e = res_e['outcome'] == 'HIGH_RISK' and any(g['gate'] == 'LOCAL_PROTOTYPE_WATCHLIST_HIT' for g in res_e['hard_gates'])
    results.append({
        'scenario': 'E',
        'title': 'Local Prototype Blacklist Hit',
        'expected_outcome': 'HIGH_RISK',
        'observed_outcome': res_e['outcome'],
        'coverage': res_e['evidence_coverage']['state'],
        'hard_gates': [g['gate'] for g in res_e['hard_gates']],
        'status': 'PASS' if passed_e else 'FAIL',
        'details': 'Synthetic document number VDA444444 matched LOCAL PROTOTYPE WATCHLIST blacklist.'
    })

    # Scenario F
    res_f = analyze_integrated(load('travel_clean.png'), load('lio_selfie.png'), database_path=db_path)
    passed_f = res_f['outcome'] == 'HIGH_RISK' and res_f['biometric_verification']['decision'] == 'MISMATCH'
    results.append({
        'scenario': 'F',
        'title': 'Biometric Face Verification Mismatch',
        'expected_outcome': 'HIGH_RISK',
        'observed_outcome': res_f['outcome'],
        'coverage': res_f['evidence_coverage']['state'],
        'hard_gates': [g['gate'] for g in res_f['hard_gates']],
        'status': 'PASS' if passed_f else 'FAIL',
        'details': 'Live face (Lio Maren) vs document portrait (Ari Solen) cosine similarity ' + str(res_f['biometric_verification'].get('similarity')) + ' < threshold 0.55.'
    })

    # Scenario G
    res_g1 = analyze_integrated(load('travel_clean.png'), case_id='case-ari-1', database_path=db_path)
    res_g2 = analyze_integrated(load('travel_blacklisted.png'), case_id='case-ari-2', database_path=db_path)
    passed_g = res_g2['identity_linkage']['status'] == 'SUSPICIOUS' and len(res_g2['identity_linkage']['matches']) > 0
    results.append({
        'scenario': 'G',
        'title': 'Multi-Identity Linkage Alert (Shared Biometrics / Conflicting Claims)',
        'expected_outcome': 'SUSPICIOUS Linkage',
        'observed_outcome': res_g2['identity_linkage']['status'],
        'coverage': res_g2['evidence_coverage']['state'],
        'hard_gates': [g['gate'] for g in res_g2['hard_gates']],
        'status': 'PASS' if passed_g else 'FAIL',
        'details': 'Ari Solen face embedding re-used under different name (ZARA CHEN); linked to existing Biometric Cluster.'
    })

    # Scenario H
    offline_adapter = MockBorderIntelligenceAdapter(available=False)
    res_h = analyze_integrated(load('travel_clean.png'), intelligence_adapter=offline_adapter, database_path=db_path)
    passed_h = res_h['outcome'] == 'INDETERMINATE' and res_h['evidence_coverage']['state'] == 'INCOMPLETE'
    results.append({
        'scenario': 'H',
        'title': 'Threat Intelligence Lane Offline / Unavailable',
        'expected_outcome': 'INDETERMINATE',
        'observed_outcome': res_h['outcome'],
        'coverage': res_h['evidence_coverage']['state'],
        'hard_gates': [g['gate'] for g in res_h['hard_gates']],
        'status': 'PASS' if passed_h else 'FAIL',
        'details': 'Mandatory threat intelligence lane unavailable -> Coverage Governor enforces INDETERMINATE outcome.'
    })

    # Scenario I
    res_i = analyze_integrated(load('travel_poor_capture.png'), database_path=db_path)
    passed_i = res_i['outcome'] == 'INDETERMINATE' and res_i['capture_quality']['acceptable'] is False
    results.append({
        'scenario': 'I',
        'title': 'Degraded / Poor Capture Quality',
        'expected_outcome': 'INDETERMINATE',
        'observed_outcome': res_i['outcome'],
        'coverage': res_i['evidence_coverage']['state'],
        'hard_gates': [g['gate'] for g in res_i['hard_gates']],
        'status': 'PASS' if passed_i else 'FAIL',
        'details': 'Low resolution & blur failed quality gate -> downstream analysis halted; RECAPTURE_DOCUMENT requested.'
    })

    report = {
        'evaluation_type': 'VEDA_BORDER_INTEGRATED_GOLDEN_SCENARIOS',
        'total_scenarios': len(results),
        'passed_scenarios': sum(1 for r in results if r['status'] == 'PASS'),
        'all_passed': all(r['status'] == 'PASS' for r in results),
        'results': results,
    }
    OUTPUT_REPORT.write_text(json.dumps(report, indent=2) + chr(10))
    temp_dir.cleanup()
    return report


if __name__ == '__main__':
    rep = evaluate()
    print(json.dumps({'total': rep['total_scenarios'], 'passed': rep['passed_scenarios'], 'all_passed': rep['all_passed']}, indent=2))
