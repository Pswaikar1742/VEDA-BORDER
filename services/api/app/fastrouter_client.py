import json
import time
from typing import Any, Dict, List, Optional
import httpx

from app.config import settings


_FORBIDDEN = ("authentic", "genuine", "legally verified", "interpol", "red notice")


def _valid_explanation(value: Any, sanitized: Dict[str, Any]) -> bool:
    if not isinstance(value, dict) or set(value) - {"status", "summary", "why_outcome", "key_evidence", "contradictions", "recommended_actions", "limitations"}:
        return False
    if value.get("status") != "ACTIVE" or not isinstance(value.get("summary"), str) or not isinstance(value.get("why_outcome"), str):
        return False
    for key in ("key_evidence", "contradictions", "recommended_actions", "limitations"):
        if not isinstance(value.get(key), list) or len(value[key]) > 10:
            return False
        if any(not isinstance(item, (str, dict)) or len(str(item)) > 600 for item in value[key]):
            return False
    ids = {str(k) for k in sanitized.get("evidence_ids", [])}
    for item in value["key_evidence"]:
        if isinstance(item, dict) and item.get("evidence_id") not in ids:
            return False
    text = json.dumps(value).lower()
    if any(word in text for word in _FORBIDDEN):
        return False
    outcome = str(sanitized.get("policy", {}).get("outcome", ""))
    if outcome in {"HIGH_RISK", "REFER", "INDETERMINATE"} and "low risk" in text:
        return False
    return True


def build_sanitized_ai_input(analysis: Dict[str, Any], family: str = "TRAVEL_DOCUMENT") -> Dict[str, Any]:
    """Sanitize analysis before sending to FastRouter AI.
    Strictly excludes raw images, face embeddings, and unnecessary PII.
    """
    coverage = analysis.get("evidence_coverage", {})
    capture = analysis.get("capture_quality", {})
    mrz = analysis.get("mrz", {})
    checks = mrz.get("checks", {})
    mrz_valid = sum(1 for v in checks.values() if v == "PASS")
    mrz_total = len(checks)
    mrz_summary = f"{mrz_valid}/{mrz_total}" if mrz_total > 0 else "N/A"

    consistency = analysis.get("cross_source_consistency", [])
    mismatches = [item.get("field") for item in consistency if item.get("status") in {"FAIL", "SUSPICIOUS"}]
    consistency_status = "CRITICAL_CONTRADICTION" if mismatches and any("CRITICAL" in str(g.get("gate", "")) for g in analysis.get("hard_gates", [])) else ("FAIL" if mismatches else ("UNAVAILABLE" if any(item.get("status") == "UNAVAILABLE" for item in consistency) or (mrz.get("mrz_detected") is False and family == "TRAVEL_DOCUMENT") else ("PASS" if consistency else "NOT_APPLICABLE")))

    biometric = analysis.get("biometric_verification", {})
    bio_decision = biometric.get("decision", "NOT_SUPPLIED")
    bio_status = biometric.get("status", "UNAVAILABLE")

    visual = analysis.get("visual_forensics", {})
    vis_status = visual.get("status", "UNAVAILABLE")

    intel = analysis.get("threat_intelligence", {})
    intel_res = intel.get("result") if intel.get("status") == "FAIL" else ("NO_LOCAL_MATCH" if intel.get("status") == "PASS" else "UNAVAILABLE")

    linkage = analysis.get("identity_linkage", {})
    link_matches = len(linkage.get("matches", []))

    hard_gates = [g.get("gate", g.get("reason", "GATE")) for g in analysis.get("hard_gates", [])]

    return {
        "case_context": {
            "document_family": family,
            "coverage": coverage.get("state", "COMPLETE"),
        },
        "evidence": {
            "capture_quality": capture.get("status", "UNAVAILABLE"),
            "mrz": {
                "status": "PASS" if mrz_valid == mrz_total and mrz_total > 0 else ("FAIL" if mrz.get("mrz_detected") else ("UNAVAILABLE" if family == "TRAVEL_DOCUMENT" else "NOT_APPLICABLE")),
                "check_digits": mrz_summary,
            },
            "cross_source_consistency": {
                "status": consistency_status,
                "contradicting_fields": mismatches,
            },
            "biometric": bio_decision if bio_status == "PASS" else bio_status,
            "visual_forensics": vis_status,
            "watchlist": intel_res if intel.get("status") == "PASS" else "UNAVAILABLE",
            "identity_linkage": f"{link_matches} alias matches" if link_matches > 0 else ("NO_MATCH" if linkage.get("status") == "PASS" else "UNAVAILABLE"),
        },
            "policy": {
            "outcome": analysis.get("outcome", "INDETERMINATE"),
            "hard_gates": hard_gates,
            "outcome_reasons": analysis.get("outcome_reasons", []),
            },
        "evidence_ids": ["capture.quality", "document.extraction.result", "document.mrz.result", "document.validation", "cross_source.consistency", "forensics.visual", "biometrics.face_verify", "threat_intelligence.local_lookup", "identity_linkage.match"],
    }


class FastRouterClient:
    """Bounded AI reasoning and explanatory support provider.
    
    ARCHITECTURAL BOUNDARIES:
    - Never authenticates documents or overrides deterministic forensic evidence.
    - Never alters MRZ, check digits, biometrics, or hard-gate decisions.
    - Used strictly for officer-facing plain English summaries and hypothesis explanation.
    - Degrades safely to UNAVAILABLE upon any network or provider failure.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.fast_router_api_key
        self.base_url = (base_url or settings.fast_router_base_url or "https://api.fastrouter.ai/api/v1").rstrip("/")
        self.model = model or settings.fast_router_model or "fastrouter/auto"
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else getattr(settings, "fast_router_timeout_seconds", 25.0)

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

    def generate_bounded_autopsy_explanation(
        self,
        sanitized_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Explain the already-decided forensic outcome using only the supplied sanitized evidence."""
        if not self.is_enabled:
            return {
                "status": "UNAVAILABLE",
                "summary": None,
                "why_outcome": None,
                "key_evidence": [],
                "contradictions": [],
                "recommended_actions": [],
                "limitations": ["FastRouter AI reasoning layer is unconfigured or disabled; core forensic rules remain fully active."],
                "model_used": None,
            }

        system_instruction = (
            "You are the VEDA-BORDER Bounded AI Forensic Reasoning Assistant for border control officers.\n"
            "Your task is to explain the ALREADY-DECIDED forensic screening outcome using ONLY the supplied structured evidence.\n"
            "RULES:\n"
            "1. Do not invent evidence or facts.\n"
            "2. Do not change the outcome or override policy/gates.\n"
            "3. Do not claim legal authenticity or absolute fraud.\n"
            "4. If evidence is missing or incomplete, state that explicitly.\n"
            "5. Respond with a valid JSON object ONLY with the following exact keys:\n"
            "   - 'status': 'ACTIVE'\n"
            "   - 'summary': string (concise 1-2 sentence executive case summary for officer)\n"
            "   - 'why_outcome': string (clear explanation of why the final triage outcome was reached)\n"
            "   - 'key_evidence': list of strings (bullet points of verified supporting evidence)\n"
            "   - 'contradictions': list of strings (bullet points of any hard or soft contradictions found, or empty list if none)\n"
            "   - 'recommended_actions': list of strings (actionable next steps for the front-line/secondary officer)\n"
            "   - 'limitations': list of strings (boundaries, e.g. research prototype, mock watchlist)\n"
        )

        prompt = f"Sanitized Evidence Dossier:\n```json\n{json.dumps(sanitized_input, indent=2)}\n```\n\nGenerate the bounded JSON explanation:"

        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 500,
            "temperature": 0.1,
        }

        t0 = time.time()
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.post(endpoint, json=payload, headers=self._headers())
                latency_ms = round((time.time() - t0) * 1000, 2)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    raw_content = choices[0]["message"]["content"] if choices else "{}"
                    try:
                        cleaned = raw_content.strip()
                        if cleaned.startswith("```"):
                            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                        parsed = json.loads(cleaned)
                        if not _valid_explanation(parsed, sanitized_input):
                            raise ValueError("AI response failed the bounded schema or evidence-reference checks")
                        return {
                            "status": "ACTIVE",
                            "summary": parsed.get("summary", ""),
                            "why_outcome": parsed.get("why_outcome", ""),
                            "key_evidence": parsed.get("key_evidence", []),
                            "contradictions": parsed.get("contradictions", []),
                            "recommended_actions": parsed.get("recommended_actions", []),
                            "limitations": parsed.get("limitations", ["Bounded AI explanation; human review mandatory."]),
                            "model_used": data.get("model", self.model),
                            "latency_ms": latency_ms,
                        }
                    except (json.JSONDecodeError, ValueError, TypeError, KeyError):
                        return {
                            "status": "DEGRADED",
                            "summary": "AI explanation was unavailable; the deterministic screening result remains authoritative.",
                            "why_outcome": "The provider returned a response that could not be validated against the evidence contract.",
                            "key_evidence": [],
                            "contradictions": sanitized_input.get("policy", {}).get("outcome_reasons", []),
                            "recommended_actions": [],
                            "limitations": ["FastRouter response failed strict validation; local deterministic evidence remains authoritative."],
                            "model_used": data.get("model", self.model),
                            "latency_ms": latency_ms,
                        }
                else:
                    return {
                        "status": "DEGRADED",
                        "summary": None,
                        "why_outcome": None,
                        "key_evidence": [],
                        "contradictions": [],
                        "recommended_actions": [],
                        "limitations": [f"Provider HTTP status {resp.status_code}"],
                        "error": f"Provider HTTP {resp.status_code}",
                        "latency_ms": latency_ms,
                    }
        except Exception as exc:
            return {
                "status": "DEGRADED",
                "summary": None,
                "why_outcome": None,
                "key_evidence": [],
                "contradictions": [],
                "recommended_actions": [],
                "limitations": [f"Provider error: {type(exc).__name__}"],
                "error": type(exc).__name__,
                "latency_ms": round((time.time() - t0) * 1000, 2),
            }
