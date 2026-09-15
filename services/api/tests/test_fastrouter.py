import os
from unittest.mock import patch, MagicMock
import pytest

from app.fastrouter_client import FastRouterClient
from app.config import settings


def test_fastrouter_unconfigured():
    client = FastRouterClient(api_key="")
    assert not client.is_configured
    assert not client.is_enabled
    res = client.test_connectivity()
    assert res["status"] == "UNCONFIGURED"
    assert not res["success"]


def test_fastrouter_graceful_degradation():
    client = FastRouterClient(api_key="dummy_key")
    # Calling generate_explanation when disabled returns UNAVAILABLE without exception
    with patch.object(settings, "fast_router_enabled", False):
        res = client.generate_explanation("Explain evidence")
        assert res["status"] == "UNAVAILABLE"
        assert res["explanation"] is None


def test_fastrouter_error_handling():
    client = FastRouterClient(api_key="dummy_key", base_url="https://invalid.domain.test/v1")
    with patch.object(settings, "fast_router_enabled", True):
        res = client.generate_explanation("Explain evidence")
        assert res["status"] == "DEGRADED"
        assert res["explanation"] is None
        assert "error" in res


def test_fastrouter_connectivity_if_env_present():
    client = FastRouterClient()
    if not client.is_configured:
        pytest.skip("FastRouter credentials not configured in environment.")

    res = client.test_connectivity()
    assert res["success"] is True
    assert res["status"] == "CONNECTED"
    assert res["http_status_class"] == "2xx"
    assert "latency_ms" in res


def test_build_sanitized_ai_input():
    from app.fastrouter_client import build_sanitized_ai_input

    sample_analysis = {
        "evidence_coverage": {"state": "COMPLETE"},
        "capture_quality": {"status": "PASS"},
        "mrz": {"mrz_detected": True, "checks": {"composite": "PASS", "dob": "PASS"}},
        "cross_source_consistency": [{"field": "date_of_birth", "status": "FAIL"}],
        "biometric_verification": {"status": "PASS", "decision": "MATCH"},
        "visual_forensics": {"status": "PASS"},
        "threat_intelligence": {"status": "PASS", "result": "CLEAR"},
        "identity_linkage": {"matches": []},
        "hard_gates": [{"gate": "CRITICAL_CROSS_SOURCE_CONTRADICTION", "reason": "DOB mismatch"}],
        "outcome": "HIGH_RISK",
        "outcome_reasons": ["Visible DOB does not match MRZ DOB"],
    }
    sanitized = build_sanitized_ai_input(sample_analysis, "TRAVEL_DOCUMENT")
    assert sanitized["case_context"]["document_family"] == "TRAVEL_DOCUMENT"
    assert sanitized["evidence"]["cross_source_consistency"]["status"] == "CRITICAL_CONTRADICTION"
    assert "date_of_birth" in sanitized["evidence"]["cross_source_consistency"]["contradicting_fields"]
    assert sanitized["policy"]["outcome"] == "HIGH_RISK"
    # Ensure no raw pixel arrays, base64 images, or embeddings exist
    assert "_embedding" not in str(sanitized)
    assert "specimen_bytes" not in str(sanitized)


def test_bounded_autopsy_explanation_degraded():
    client = FastRouterClient(api_key="dummy_key", base_url="https://invalid.domain.test/v1")
    with patch.object(settings, "fast_router_enabled", True):
        res = client.generate_bounded_autopsy_explanation({"case_context": {}, "evidence": {}, "policy": {}})
        assert res["status"] == "DEGRADED"
        assert res["summary"] is None
