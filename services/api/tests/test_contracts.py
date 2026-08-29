import hashlib
from app.contracts import EvidenceState, ScreeningOutcome, build_placeholder_autopsy


def test_sha256_is_deterministic():
    assert hashlib.sha256(b"fictional specimen").hexdigest() == hashlib.sha256(b"fictional specimen").hexdigest()


def test_status_enum_serializes_exactly():
    assert EvidenceState.UNAVAILABLE.value == "UNAVAILABLE"
    assert ScreeningOutcome.INDETERMINATE.value == "INDETERMINATE"


def test_required_unavailable_cannot_clear():
    result = build_placeholder_autopsy("scan-1", "demo.png", "a" * 64)
    assert result.outcome == ScreeningOutcome.INDETERMINATE
    assert result.evidence_coverage.missing_mandatory
    assert result.outcome != ScreeningOutcome.CLEAR

