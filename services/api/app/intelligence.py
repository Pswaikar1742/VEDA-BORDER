from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class IntelligenceResult(str, Enum):
    CLEAR = "CLEAR"
    DOCUMENT_BLACKLISTED = "DOCUMENT_BLACKLISTED"
    IDENTITY_WATCHLIST_MATCH = "IDENTITY_WATCHLIST_MATCH"
    UNAVAILABLE = "UNAVAILABLE"


class ThreatIntelligenceAdapter(ABC):
    @abstractmethod
    def check(self, document_number: str | None, holder_name: str | None) -> dict[str, Any]:
        """Return demo intelligence evidence without accessing a real system."""


class MockBorderIntelligenceAdapter(ThreatIntelligenceAdapter):
    """Local-only synthetic lookup. This is not a government integration."""

    source = "MOCK_BORDER_INTELLIGENCE"
    blacklisted_documents = frozenset({"VDA444444", "DEMO-BLACKLIST-77"})
    watched_identities = frozenset({"WATCH DEMO", "SYNTHETIC ALERT"})

    def __init__(self, available: bool = True) -> None:
        self.available = available

    def _lookup(self, query_type: str, identifier: str | None, result: IntelligenceResult, reason: str) -> dict[str, str | bool | None]:
        return {
            "query_type": query_type,
            "queried_synthetic_identifier": identifier,
            "source": self.source,
            "result": result.value,
            "reason": reason,
            "lookup_timestamp": datetime.now(timezone.utc).isoformat(),
            "demo_mock": True,
        }

    def check(self, document_number: str | None, holder_name: str | None) -> dict[str, Any]:
        if not self.available:
            lookup = self._lookup("AVAILABILITY", None, IntelligenceResult.UNAVAILABLE, "DEMO mock intelligence adapter is disabled.")
            return {"source": self.source, "demo_data": True, "status": "UNAVAILABLE", "result": IntelligenceResult.UNAVAILABLE.value, "reason": lookup["reason"], "lookups": [lookup]}

        normalized_document = "".join((document_number or "").upper().split()) or None
        normalized_name = " ".join((holder_name or "").upper().split()) or None
        if not normalized_document and not normalized_name:
            result = IntelligenceResult.UNAVAILABLE
            reason = "No synthetic identifier was available for the DEMO mock lookup."
            status = "UNAVAILABLE"
        elif normalized_document in self.blacklisted_documents:
            result = IntelligenceResult.DOCUMENT_BLACKLISTED
            reason = "Synthetic document number is listed in the local DEMO blacklist."
            status = "FAIL"
        elif normalized_name in self.watched_identities:
            result = IntelligenceResult.IDENTITY_WATCHLIST_MATCH
            reason = "Synthetic identity is listed in the local DEMO watchlist."
            status = "FAIL"
        else:
            result = IntelligenceResult.CLEAR
            reason = "No match in the local synthetic DEMO intelligence records."
            status = "PASS"
        queried_identifier = normalized_name if result == IntelligenceResult.IDENTITY_WATCHLIST_MATCH else (normalized_document or normalized_name)
        lookup = self._lookup("DOCUMENT_AND_IDENTITY", queried_identifier, result, reason)
        return {"source": self.source, "demo_data": True, "status": status, "result": result.value, "reason": reason, "lookups": [lookup]}
