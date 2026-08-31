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
    env_path = os.path.expanduser("~/.config/veda/fastrouter.env")
    api_key = ""
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if "FASTROUTER_API_KEY" in line and "=" in line:
                    api_key = line.replace("export ", "").split("=", 1)[1].strip().strip('"').strip("'")

    if not api_key:
        pytest.skip("FastRouter credentials not configured in environment.")

    client = FastRouterClient(api_key=api_key)
    res = client.test_connectivity()
    assert res["success"] is True
    assert res["status"] == "CONNECTED"
    assert res["http_status_class"] == "2xx"
    assert "latency_ms" in res
