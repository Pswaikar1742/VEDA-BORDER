from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response

from app.autopsy import build_integrated_autopsy
from app.config import resolve_repo_path, settings
from app.contracts import IdentityForensicAutopsy
from app.integrated_pipeline import analyze_integrated
from app.linkage import LocalIdentityLinkageStore
from app.persistence import CaseRepository
from app.reporting import render_printable_html
from app.system_status import module_status


router = APIRouter(prefix="/api/v1", tags=["workspace"])
IMAGE_TYPES = {"image/png", "image/jpeg"}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024


def _repository() -> CaseRepository:
    return CaseRepository(settings.case_database_path)


def _decode_document(data: bytes, filename: str, content_type: str | None) -> bytes:
    suffix = Path(filename).suffix.lower()
    if content_type in IMAGE_TYPES or suffix in {".png", ".jpg", ".jpeg"}:
        return data
    if content_type == "application/pdf" or suffix == ".pdf":
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory) / "document.pdf"
            output = Path(directory) / "page"
            pdf.write_bytes(data)
            result = subprocess.run(["pdftoppm", "-f", "1", "-singlefile", "-png", "-r", "160", str(pdf), str(output)], capture_output=True, check=False, timeout=30)
            png = output.with_suffix(".png")
            if result.returncode != 0 or not png.is_file():
                raise HTTPException(status_code=422, detail="The first PDF page could not be rendered locally.")
            return png.read_bytes()
    raise HTTPException(status_code=415, detail="Unsupported specimen type; use PNG, JPG, or PDF.")


@router.post("/screenings", response_model=IdentityForensicAutopsy)
async def create_screening(
    file: UploadFile = File(...),
    selfie: UploadFile | None = File(default=None),
    document_family: str | None = Form(default=None),
) -> IdentityForensicAutopsy:
    original = await file.read()
    if not original:
        raise HTTPException(status_code=400, detail="Document file is empty.")
    if len(original) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Document exceeds the 15 MiB local prototype limit.")
    pixels = _decode_document(original, file.filename or "unnamed", file.content_type)
    selfie_bytes = await selfie.read() if selfie else None
    if selfie_bytes and len(selfie_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Face image exceeds the 15 MiB local prototype limit.")
    case_id = str(uuid4())
    digest = hashlib.sha256(original).hexdigest()
    try:
        analysis = analyze_integrated(pixels, selfie_bytes, document_family, case_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    autopsy = build_integrated_autopsy(case_id, file.filename or "unnamed", digest, analysis, bool(selfie_bytes))
    _repository().save(autopsy.model_dump(mode="json"))
    return autopsy


@router.get("/cases")
def list_cases(limit: int = 50) -> dict:
    repository = _repository()
    return {"cases": repository.list(max(1, min(limit, 200))), "summary": repository.summary()}


@router.get("/cases/{case_id}")
def get_case(case_id: str) -> dict:
    result = _repository().get(case_id)
    if not result:
        raise HTTPException(status_code=404, detail="Case not found.")
    return result


@router.get("/cases/{case_id}/report.json")
def export_case_json(case_id: str) -> Response:
    result = get_case(case_id)
    return Response(json.dumps(result, indent=2), media_type="application/json", headers={"Content-Disposition": f'attachment; filename="veda-border-{case_id}.json"'})


@router.get("/cases/{case_id}/report.html", response_class=HTMLResponse)
def export_case_html(case_id: str) -> HTMLResponse:
    return HTMLResponse(render_printable_html(get_case(case_id)), headers={"Content-Disposition": f'inline; filename="veda-border-{case_id}.html"'})


@router.get("/identity-linkage")
def identity_linkage() -> dict:
    return {"source": "LOCAL PROTOTYPE IDENTITY LINKAGE", "clusters": LocalIdentityLinkageStore(settings.case_database_path, settings.identity_linkage_threshold).clusters()}


@router.get("/system/status")
def system_readiness() -> dict:
    return module_status()


@router.get("/fixtures")
def list_fixtures() -> dict:
    fixtures_dir = Path(resolve_repo_path("data/integrated_fixtures"))
    manifest_file = fixtures_dir / "manifest.json"
    manifest = json.loads(manifest_file.read_text()) if manifest_file.is_file() else {}
    files = []
    if fixtures_dir.is_dir():
        for p in sorted(fixtures_dir.glob("*.png")):
            files.append({
                "filename": p.name,
                "url": f"/api/v1/fixtures/{p.name}",
                "size_bytes": p.stat().st_size,
            })
    return {"manifest": manifest, "fixtures": files}


@router.get("/fixtures/{filename}")
def get_fixture_file(filename: str):
    fixtures_dir = Path(resolve_repo_path("data/integrated_fixtures"))
    file_path = fixtures_dir / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Fixture file not found.")
    return FileResponse(str(file_path), media_type="image/png")
