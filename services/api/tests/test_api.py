import asyncio
import hashlib
from app.main import app
from app.routes.health import health
from app.routes.scan import scan_specimen


class FakeUpload:
    def __init__(self, filename: str, content_type: str, data: bytes):
        self.filename = filename
        self.content_type = content_type
        self._data = data

    async def read(self) -> bytes:
        return self._data


def test_health_endpoint():
    assert health()["status"] == "ok"
    assert "/health" in {route.path for route in app.routes}


def test_scan_returns_typed_indeterminate_autopsy():
    upload = FakeUpload("demo.png", "image/png", b"synthetic bytes")
    body = asyncio.run(scan_specimen(upload)).model_dump(mode="json")
    assert body["specimen_filename"] == "demo.png"
    assert body["specimen_sha256"] == hashlib.sha256(b"synthetic bytes").hexdigest()
    assert body["outcome"] == "INDETERMINATE"
    assert any(lane["status"] == "UNAVAILABLE" for lane in body["evidence_lanes"])


def test_scan_rejects_unsupported_type():
    from fastapi import HTTPException
    upload = FakeUpload("demo.txt", "text/plain", b"not allowed")
    try:
        asyncio.run(scan_specimen(upload))
    except HTTPException as error:
        assert error.status_code == 415
    else:
        raise AssertionError("unsupported file type was accepted")
