import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.biometrics import OpenCvSFaceAdapter
from app.config import resolve_repo_path, settings
from app.contracts import DocumentFamily
from app.document_families import classify_document, get_adapter
from app.evidence_graph import SOURCE_TIERS, build_evidence_graph
from app.integrated_pipeline import analyze_integrated
from app.intelligence import MockBorderIntelligenceAdapter
from app.linkage import LocalIdentityLinkageStore
from app.main import app
from app.persistence import CaseRepository
from app.policy import build_coverage, build_hypotheses, evaluate_hard_gates, plan_next_actions, triage_outcome
from app.quality import assess_capture_quality
from app.reporting import render_printable_html
from app.system_status import module_status
from app.visual_forensics import LocalDeterministicVisualForensics

FIXTURES_DIR = Path(resolve_repo_path('data/integrated_fixtures'))


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def temp_db(tmp_path):
    return str(tmp_path / 'test_veda.db')


def load_fixture(filename: str) -> bytes:
    path = FIXTURES_DIR / filename
    if not path.is_file():
        pytest.skip(f'Fixture {filename} not found at {path}')
    return path.read_bytes()


# =====================================================================
# 1. DOCUMENT FAMILIES TESTS
# =====================================================================

def test_document_families_adapters():
    travel = get_adapter(DocumentFamily.TRAVEL_DOCUMENT)
    assert travel.supports_mrz is True
    assert 'date_of_birth' in travel.required_fields
    assert travel.applicability()['mrz'] == 'APPLICABLE'

    visa = get_adapter(DocumentFamily.VISA_OR_PERMIT)
    assert visa.supports_mrz is False
    assert visa.applicability()['mrz'] == 'NOT_APPLICABLE'

    nid = get_adapter(DocumentFamily.NATIONAL_ID)
    assert nid.supports_mrz is False

    dl = get_adapter(DocumentFamily.DRIVING_LICENCE)
    assert dl.supports_mrz is False

    with pytest.raises(ValueError, match='Unsupported document family'):
        get_adapter('UNKNOWN_FAMILY')


def test_document_family_classification():
    travel_ocr = 'P<NSLSOLEN<<ARI<<<<<<<<<<<<<<<<<<<<<<<<<<<<< VEDA-BORDERSYNTHETIC TRAVEL'
    res = classify_document(travel_ocr)
    assert res['family'] == DocumentFamily.TRAVEL_DOCUMENT.value

    visa_ocr = 'VISA OR PERMIT ENTRY PERMIT'
    res_visa = classify_document(visa_ocr)
    assert res_visa['family'] == DocumentFamily.VISA_OR_PERMIT.value

    manual = classify_document('GARBAGE OCR', manual_override='NATIONAL_ID')
    assert manual['family'] == 'NATIONAL_ID'
    assert manual['method'] == 'MANUAL_OVERRIDE'


# =====================================================================
# 2. CAPTURE QUALITY TESTS
# =====================================================================

def test_capture_quality_acceptable():
    clean_bytes = load_fixture('travel_clean.png')
    quality = assess_capture_quality(clean_bytes, 700, 440)
    assert quality['acceptable'] is True
    assert quality['status'] in {'PASS', 'SUSPICIOUS'}
    assert quality['recommendation'] is None


def test_capture_quality_poor_capture():
    poor_bytes = load_fixture('travel_poor_capture.png')
    quality = assess_capture_quality(poor_bytes, 700, 440)
    assert quality['acceptable'] is False
    assert quality['status'] == 'FAIL'
    assert quality['recommendation'] == 'RECAPTURE_DOCUMENT'


def test_capture_quality_invalid_bytes():
    quality = assess_capture_quality(b'not an image', 700, 440)
    assert quality['acceptable'] is False
    assert quality['status'] == 'FAILED_TO_EXECUTE'
    assert quality['recommendation'] == 'RECAPTURE_DOCUMENT'


# =====================================================================
# 3. BIOMETRICS TESTS
# =====================================================================

def test_biometrics_face_verification():
    doc_bytes = load_fixture('travel_clean.png')
    ari_bytes = load_fixture('ari_selfie.png')
    lio_bytes = load_fixture('lio_selfie.png')

    adapter = OpenCvSFaceAdapter(settings.face_detector_model, settings.face_recognizer_model, threshold=0.55, enabled=True)
    assert adapter.ready() is True

    # Same identity match
    res_match = adapter.verify(doc_bytes, ari_bytes, (0.055, 0.245, 0.260, 0.690))
    assert res_match['status'] == 'PASS'
    assert res_match['decision'] == 'MATCH'
    assert res_match['similarity'] >= 0.55
    assert '_embedding' in res_match

    # Different identity mismatch
    res_mismatch = adapter.verify(doc_bytes, lio_bytes, (0.055, 0.245, 0.260, 0.690))
    assert res_mismatch['status'] == 'FAIL'
    assert res_mismatch['decision'] == 'MISMATCH'
    assert res_mismatch['similarity'] < 0.55

    # Missing live face
    res_no_selfie = adapter.verify(doc_bytes, None, (0.055, 0.245, 0.260, 0.690))
    assert res_no_selfie['status'] == 'UNAVAILABLE'
    assert res_no_selfie['decision'] == 'UNAVAILABLE'

    # Disabled biometrics
    disabled_adapter = OpenCvSFaceAdapter(settings.face_detector_model, settings.face_recognizer_model, threshold=0.55, enabled=False)
    assert disabled_adapter.ready() is False
    res_disabled = disabled_adapter.verify(doc_bytes, ari_bytes, (0.055, 0.245, 0.260, 0.690))
    assert res_disabled['status'] == 'UNAVAILABLE'


# =====================================================================
# 4. VISUAL FORENSICS TESTS
# =====================================================================

def test_visual_forensics_clean_and_tampered():
    clean_bytes = load_fixture('travel_clean.png')
    tampered_bytes = load_fixture('travel_portrait_replaced.png')

    engine = LocalDeterministicVisualForensics()

    res_clean = engine.analyze(clean_bytes)
    assert res_clean['status'] == 'PASS'
    assert len(res_clean['findings']) == 0

    res_tampered = engine.analyze(tampered_bytes)
    assert res_tampered['status'] == 'SUSPICIOUS'
    assert len(res_tampered['findings']) > 0
    assert any('PORTRAIT' in f.get('finding_type', '') for f in res_tampered['findings'])

    # Corrupted / invalid image
    res_invalid = engine.analyze(b'corrupt')
    assert res_invalid['status'] == 'UNAVAILABLE'


# =====================================================================
# 5. IDENTITY LINKAGE TESTS
# =====================================================================

def test_identity_linkage_store(temp_db):
    store = LocalIdentityLinkageStore(temp_db, threshold=0.50)
    embedding_a = [0.8] * 128
    # Enrol first identity
    res1 = store.search_and_enrol('case-001', 'ALICE SMITH', 'DOC111111', embedding_a)
    assert res1['status'] == 'PASS'
    assert len(res1['matches']) == 0
    assert 'Biometric Cluster' in res1['identity_reference']

    # Enrol same embedding with DIFFERENT claimed name & doc number -> MULTI IDENTITY ALERT
    res2 = store.search_and_enrol('case-002', 'BOB JONES', 'DOC222222', embedding_a)
    assert res2['status'] == 'SUSPICIOUS'
    assert len(res2['matches']) == 1
    assert res2['matches'][0]['finding'] == 'POSSIBLE_MULTI_IDENTITY_LINKAGE'
    assert res2['matches'][0]['case_id'] == 'case-001'

    # Verify clusters
    clusters = store.clusters()
    assert len(clusters) >= 1
    assert len(clusters[0]['credentials']) == 2


# =====================================================================
# 6. EVIDENCE GRAPH & TIERS TESTS
# =====================================================================

def test_evidence_graph_building():
    analysis = {
        'extraction': {'visible_fields': {'holder_name': 'ARI SOLEN', 'date_of_birth': '1994-03-17'}},
        'mrz': {'fields': {'holder_name': 'ARI SOLEN', 'date_of_birth': '1994-03-17'}},
        'cross_source_consistency': [
            {'field': 'holder_name', 'status': 'PASS'},
            {'field': 'date_of_birth', 'status': 'PASS'},
        ],
        'visual_forensics': {'status': 'PASS'},
        'biometric_verification': {'status': 'PASS'},
        'threat_intelligence': {'status': 'PASS'},
        'identity_linkage': {'status': 'PASS'},
    }
    graph = build_evidence_graph(analysis)
    assert 'nodes' in graph and 'edges' in graph
    assert SOURCE_TIERS['MRZ'] == 2
    assert SOURCE_TIERS['VIZ_OCR'] == 3
    assert SOURCE_TIERS['BIOMETRIC_VERIFICATION'] == 4
    assert SOURCE_TIERS['ELECTRONIC_CREDENTIAL'] == 1


# =====================================================================
# 7. FORENSIC HYPOTHESIS & NEXT-BEST-ACTIONS TESTS
# =====================================================================

def test_hypotheses_and_actions():
    analysis = {
        'capture_quality': {'acceptable': True},
        'cross_source_consistency': [
            {'field': 'date_of_birth', 'status': 'FAIL', 'severity': 'CRITICAL', 'reason': 'DOB mismatch'}
        ],
        'visual_forensics': {'status': 'SUSPICIOUS'},
        'biometric_verification': {'status': 'FAIL', 'decision': 'MISMATCH', 'reason': 'Biometric mismatch'},
        'threat_intelligence': {'status': 'PASS'},
        'identity_linkage': {'status': 'SUSPICIOUS'},
        'document_rules': [],
    }
    coverage = {'state': 'INCOMPLETE', 'missing_mandatory': ['electronic_credential']}
    hypotheses = build_hypotheses(analysis, coverage)
    hyp_names = [h['hypothesis'] for h in hypotheses]
    assert 'POSSIBLE_VISIBLE_BIOGRAPHIC_FIELD_ALTERATION' in hyp_names
    assert 'POSSIBLE_PORTRAIT_SUBSTITUTION' in hyp_names
    assert 'POSSIBLE_DOCUMENT_REGION_MANIPULATION' in hyp_names
    assert 'POSSIBLE_MULTI_IDENTITY_USAGE' in hyp_names

    hard_gates = evaluate_hard_gates(analysis, coverage, biometric_required=True)
    actions = plan_next_actions(analysis, coverage, hard_gates)
    action_names = [a['action'] for a in actions]
    assert 'RECAPTURE_FIELD_REGION' in action_names
    assert 'REFER_TO_SECONDARY_INSPECTION' in action_names


# =====================================================================
# 8. PERSISTENCE & REPORTING TESTS
# =====================================================================

def test_persistence_and_reporting(temp_db):
    repo = CaseRepository(temp_db)
    autopsy_data = {
        'case_id': 'test-case-100',
        'created_at': '2026-08-30T10:00:00Z',
        'document_family': 'TRAVEL_DOCUMENT',
        'outcome': 'LOW_RISK',
        'specimen_filename': 'travel_clean.png',
        'specimen_sha256': 'abcdef123456',
        'visible_document_data': {'visible_fields': {'holder_name': 'TEST USER', 'document_number': 'VDA100'}},
        'critical_findings': [],
        'evidence_coverage': {'coverage_ratio': 1.0, 'state': 'COMPLETE', 'missing_mandatory': []},
        'disclaimer': 'Research-prototype only.',
    }
    repo.save(autopsy_data)

    retrieved = repo.get('test-case-100')
    assert retrieved is not None
    assert retrieved['case_id'] == 'test-case-100'
    assert retrieved['outcome'] == 'LOW_RISK'

    cases_list = repo.list()
    assert len(cases_list) == 1
    assert cases_list[0]['case_id'] == 'test-case-100'

    summary = repo.summary()
    assert summary['cases_screened'] == 1
    assert summary['low_risk'] == 1

    # Render HTML report
    html_output = render_printable_html(autopsy_data)
    assert '<!doctype html>' in html_output
    assert 'VEDA-BORDER' in html_output
    assert 'test-case-100' in html_output


# =====================================================================
# 9. SYSTEM STATUS TESTS
# =====================================================================

def test_system_status():
    status = module_status()
    assert 'status' in status
    assert 'modules' in status
    module_names = [m['module'] for m in status['modules']]
    assert 'OCR' in module_names
    assert 'MRZ' in module_names
    assert 'Rules' in module_names
    assert 'Consistency' in module_names
    assert 'Visual Forensics' in module_names
    assert 'Face Verification' in module_names
    assert 'Threat Intelligence' in module_names
    assert 'Identity Linkage' in module_names
    assert 'Evidence Graph' in module_names
    assert 'Coverage Governor' in module_names


# =====================================================================
# 10. GOLDEN SCENARIOS (A TO I) INTEGRATED PIPELINE TESTS
# =====================================================================

def test_golden_scenario_a_clean_consistent(temp_db):
    doc_bytes = load_fixture('travel_clean.png')
    selfie_bytes = load_fixture('ari_selfie.png')

    analysis = analyze_integrated(doc_bytes, selfie_bytes, database_path=temp_db)
    assert analysis['capture_quality']['acceptable'] is True
    assert analysis['outcome'] == 'LOW_RISK'
    assert len(analysis['hard_gates']) == 0
    assert analysis['evidence_coverage']['state'] == 'COMPLETE'
    assert analysis['biometric_verification']['decision'] == 'MATCH'
    assert analysis['visual_forensics']['status'] == 'PASS'


def test_golden_scenario_b_dob_altered(temp_db):
    doc_bytes = load_fixture('travel_dob_altered.png')
    analysis = analyze_integrated(doc_bytes, database_path=temp_db)
    assert analysis['outcome'] == 'HIGH_RISK'
    gate_names = [g['gate'] for g in analysis['hard_gates']]
    assert 'CRITICAL_CROSS_SOURCE_CONTRADICTION' in gate_names
    dob_comp = next(c for c in analysis['cross_source_consistency'] if c['field'] == 'date_of_birth')
    assert dob_comp['status'] == 'FAIL'


def test_golden_scenario_c_portrait_replaced(temp_db):
    doc_bytes = load_fixture('travel_portrait_replaced.png')
    analysis = analyze_integrated(doc_bytes, database_path=temp_db)
    assert analysis['visual_forensics']['status'] == 'SUSPICIOUS'
    assert analysis['outcome'] == 'REFER'


def test_golden_scenario_d_expired(temp_db):
    doc_bytes = load_fixture('travel_expired.png')
    analysis = analyze_integrated(doc_bytes, database_path=temp_db)
    gate_names = [g['gate'] for g in analysis['hard_gates']]
    assert 'EXPIRED_DOCUMENT' in gate_names
    assert analysis['outcome'] in {'REFER', 'HIGH_RISK'}


def test_golden_scenario_e_blacklisted(temp_db):
    doc_bytes = load_fixture('travel_blacklisted.png')
    analysis = analyze_integrated(doc_bytes, database_path=temp_db)
    assert analysis['threat_intelligence']['result'] == 'DOCUMENT_BLACKLISTED'
    assert analysis['outcome'] == 'HIGH_RISK'
    gate_names = [g['gate'] for g in analysis['hard_gates']]
    assert 'LOCAL_PROTOTYPE_WATCHLIST_HIT' in gate_names


def test_golden_scenario_f_face_mismatch(temp_db):
    doc_bytes = load_fixture('travel_clean.png')
    mismatch_selfie = load_fixture('lio_selfie.png')
    analysis = analyze_integrated(doc_bytes, mismatch_selfie, database_path=temp_db)
    assert analysis['biometric_verification']['decision'] == 'MISMATCH'
    assert analysis['outcome'] == 'HIGH_RISK'
    gate_names = [g['gate'] for g in analysis['hard_gates']]
    assert 'REQUIRED_BIOMETRIC_MISMATCH' in gate_names


def test_golden_scenario_g_identity_linkage(temp_db):
    # Enrol Ari with first credential
    doc_a = load_fixture('travel_clean.png')
    analysis_a = analyze_integrated(doc_a, case_id='case-ari-1', database_path=temp_db)
    assert analysis_a['identity_linkage']['status'] == 'PASS'

    # Enrol Ari's face under a different synthetic document with a different name
    doc_b = load_fixture('travel_blacklisted.png')
    analysis_b = analyze_integrated(doc_b, case_id='case-ari-2', database_path=temp_db)
    assert analysis_b['identity_linkage']['status'] == 'SUSPICIOUS'
    assert len(analysis_b['identity_linkage']['matches']) > 0


def test_golden_scenario_h_intelligence_unavailable(temp_db):
    doc_bytes = load_fixture('travel_clean.png')
    offline_adapter = MockBorderIntelligenceAdapter(available=False)
    analysis = analyze_integrated(doc_bytes, intelligence_adapter=offline_adapter, database_path=temp_db)
    assert analysis['threat_intelligence']['status'] == 'UNAVAILABLE'
    assert analysis['evidence_coverage']['state'] == 'INCOMPLETE'
    assert analysis['outcome'] == 'INDETERMINATE'


def test_golden_scenario_i_poor_capture(temp_db):
    poor_bytes = load_fixture('travel_poor_capture.png')
    analysis = analyze_integrated(poor_bytes, database_path=temp_db)
    assert analysis['capture_quality']['acceptable'] is False
    assert analysis['outcome'] == 'INDETERMINATE'
    assert analysis['extraction']['visible_fields'] == {}


# =====================================================================
# 11. API INTEGRATION TESTS
# =====================================================================

def test_api_workspace_endpoints(client):
    clean_bytes = load_fixture('travel_clean.png')
    ari_bytes = load_fixture('ari_selfie.png')

    # POST /api/v1/screenings
    response = client.post(
        '/api/v1/screenings',
        files={'file': ('travel_clean.png', clean_bytes, 'image/png'), 'selfie': ('ari_selfie.png', ari_bytes, 'image/png')},
    )
    assert response.status_code == 200
    data = response.json()
    assert 'case_id' in data
    assert data['outcome'] == 'LOW_RISK'
    assert data['triage_risk_index'] == 8.0
    case_id = data['case_id']

    # GET /api/v1/cases
    res_list = client.get('/api/v1/cases')
    assert res_list.status_code == 200
    cases_data = res_list.json()
    assert any(c['case_id'] == case_id for c in cases_data['cases'])

    # GET /api/v1/cases/{case_id}
    res_case = client.get(f'/api/v1/cases/{case_id}')
    assert res_case.status_code == 200
    assert res_case.json()['case_id'] == case_id

    # GET /api/v1/cases/{case_id}/report.json
    res_json = client.get(f'/api/v1/cases/{case_id}/report.json')
    assert res_json.status_code == 200
    assert 'application/json' in res_json.headers['content-type']

    # GET /api/v1/cases/{case_id}/report.html
    res_html = client.get(f'/api/v1/cases/{case_id}/report.html')
    assert res_html.status_code == 200
    assert 'text/html' in res_html.headers['content-type']
    assert 'VEDA-BORDER' in res_html.text

    # GET /api/v1/identity-linkage
    res_linkage = client.get('/api/v1/identity-linkage')
    assert res_linkage.status_code == 200
    assert 'clusters' in res_linkage.json()

    # GET /api/v1/system/status
    res_status = client.get('/api/v1/system/status')
    assert res_status.status_code == 200
    assert 'modules' in res_status.json()

    # Error on empty file
    res_empty = client.post('/api/v1/screenings', files={'file': ('empty.png', b'', 'image/png')})
    assert res_empty.status_code == 400

    # Error on unsupported file type
    res_unsupported = client.post('/api/v1/screenings', files={'file': ('doc.txt', b'plain text', 'text/plain')})
    assert res_unsupported.status_code == 415
