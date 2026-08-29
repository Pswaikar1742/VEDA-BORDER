import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any


class LocalOcrAdapter:
    """Byte-in, text-out adapter; no filename or benchmark metadata is consulted."""

    def extract_text(self, specimen_bytes: bytes, filename: str | None = None) -> tuple[str, dict[str, Any]]:
        if specimen_bytes.lstrip().startswith(b"{"):
            try:
                payload = json.loads(specimen_bytes.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return "", {"backend": "synthetic-text-container", "error": "invalid JSON specimen"}
            return str(payload.get("visible_text", "")), {"backend": "synthetic-text-container"}
        suffix = Path(filename or "specimen.png").suffix or ".png"
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / f"specimen{suffix}"
            input_path.write_bytes(specimen_bytes)
            result = subprocess.run(["tesseract", str(input_path), "stdout", "--psm", "6"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            return "", {"backend": "tesseract", "error": result.stderr.strip()}
        return result.stdout, {"backend": "tesseract"}


def extract_visible_fields(raw_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    labels = {"holder_name": "Holder Name", "document_number": "Credential Reference", "nationality": "Nationality", "date_of_birth": "Date of Birth", "expiry_date": "Valid Until", "sex": "Sex"}
    for line in raw_text.splitlines():
        for key, label in labels.items():
            prefix = label + ":"
            if line.strip().lower().startswith(prefix.lower()):
                value = line.split(":", 1)[1].strip()
                if value:
                    fields[key] = value
    return fields


def extract_specimen(specimen_bytes: bytes, filename: str | None = None) -> dict[str, Any]:
    raw_text, ocr_meta = LocalOcrAdapter().extract_text(specimen_bytes, filename)
    return {"raw_ocr_text": raw_text, "ocr_metadata": ocr_meta, "visible_fields": extract_visible_fields(raw_text)}
