import hashlib
from uuid import uuid4
from fastapi import APIRouter, File, HTTPException, UploadFile
from app.config import settings
from app.contracts import IdentityForensicAutopsy, build_task04_autopsy
from app.intelligence import MockBorderIntelligenceAdapter
from app.pipeline import analyze_specimen

router = APIRouter(prefix="/api/v1", tags=["scan"])
SUPPORTED_TYPES = {"image/png", "image/jpeg"}
SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg"}


@router.post("/scan", response_model=IdentityForensicAutopsy)
async def scan_specimen(file: UploadFile = File(...)) -> IdentityForensicAutopsy:
    suffix = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else ""
    if file.content_type not in SUPPORTED_TYPES and suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Unsupported specimen type; use PNG, JPG, or PDF.")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Specimen file is empty.")
    digest = hashlib.sha256(data).hexdigest()
    analysis = analyze_specimen(data, MockBorderIntelligenceAdapter(available=settings.mock_border_intelligence_enabled))
    return build_task04_autopsy(str(uuid4()), file.filename or "unnamed-specimen", digest, analysis, intelligence_mandatory=settings.threat_intelligence_mandatory)
