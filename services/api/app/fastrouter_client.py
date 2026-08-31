from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
import httpx

from app.config import settings


class FastRouterClient:
    """Optional external reasoning and explanatory support provider.
    
    ARCHITECTURAL BOUNDARIES:
    - Never authenticates documents or overrides deterministic forensic evidence.
    - Never alters MRZ, check digits, biometrics, or hard-gate decisions.
    - Used strictly for officer-facing plain English summaries and hypothesis wording.
    - Degrades safely to UNAVAILABLE upon any network or provider failure.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.fast_router_api_key
        self.base_url = (base_url or settings.fast_router_base_url or "https://api.fastrouter.ai/api/v1").rstrip("/")
        self.model = model or settings.fast_router_model or "fastrouter/auto"
        self.timeout_seconds = timeout_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key.strip())

    @property
    def is_enabled(self) -> bool:
        return settings.fast_router_enabled and self.is_configured

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "VEDA-BORDER/1.0 (Forensic Screening Platform)",
        }

    def test_connectivity(self) -> Dict[str, Any]:
        """Smallest possible connectivity check without sending any document data or PII."""
        if not self.is_configured:
            return {
                "success": False,
                "status": "UNCONFIGURED",
                "detail": "FASTROUTER_API_KEY is not set in environment or config.",
                "latency_ms": 0,
            }

        endpoint = f"{self.base_url}/models"
        t0 = time.time()
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.get(endpoint, headers=self._headers())
                latency_ms = round((time.time() - t0) * 1000, 2)
                status_class = f"{resp.status_code // 100}xx"

                if resp.status_code == 200:
                    data = resp.json()
                    available_models = [m.get("id") for m in data.get("data", []) if isinstance(m, dict)]
                    return {
                        "success": True,
                        "status": "CONNECTED",
                        "http_status": resp.status_code,
                        "http_status_class": status_class,
                        "latency_ms": latency_ms,
                        "target_model": self.model,
                        "model_available": self.model in available_models if available_models else True,
                        "total_models_available": len(available_models),
                    }
                else:
                    return {
                        "success": False,
                        "status": "ERROR",
                        "http_status": resp.status_code,
                        "http_status_class": status_class,
                        "latency_ms": latency_ms,
                        "error_type": "HTTPStatusError",
                        "detail": f"Provider responded with status {resp.status_code}.",
                    }
        except httpx.TimeoutException:
            return {
                "success": False,
                "status": "TIMEOUT",
                "latency_ms": round((time.time() - t0) * 1000, 2),
                "error_type": "TimeoutException",
                "detail": f"Connection to {self.base_url} timed out after {self.timeout_seconds}s.",
            }
        except Exception as exc:
            return {
                "success": False,
                "status": "CONNECTION_FAILED",
                "latency_ms": round((time.time() - t0) * 1000, 2),
                "error_type": type(exc).__name__,
                "detail": "Network connection to FastRouter endpoint failed.",
            }

    def generate_explanation(
        self,
        prompt: str,
        system_instruction: str = "You are a forensic document screening assistant. Provide concise, factual officer summaries based strictly on verified evidence provided. Do not invent facts or override check verdicts.",
        max_tokens: int = 400,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Generate structured explanatory text over already-produced forensic evidence."""
        if not self.is_enabled:
            return {
                "status": "UNAVAILABLE",
                "explanation": None,
                "reason": "FastRouter provider is disabled or unconfigured.",
            }

        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        t0 = time.time()
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.post(endpoint, json=payload, headers=self._headers())
                latency_ms = round((time.time() - t0) * 1000, 2)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    content = choices[0]["message"]["content"] if choices else ""
                    return {
                        "status": "SUCCESS",
                        "explanation": content.strip(),
                        "model_used": data.get("model", self.model),
                        "latency_ms": latency_ms,
                    }
                else:
                    return {
                        "status": "DEGRADED",
                        "explanation": None,
                        "error": f"Provider HTTP {resp.status_code}",
                        "latency_ms": latency_ms,
                    }
        except Exception as exc:
            return {
                "status": "DEGRADED",
                "explanation": None,
                "error": type(exc).__name__,
                "latency_ms": round((time.time() - t0) * 1000, 2),
            }
