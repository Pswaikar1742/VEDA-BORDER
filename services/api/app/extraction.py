from __future__ import annotations

import csv
import re
import subprocess
import tempfile
from datetime import datetime
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError


FIELDS = ("holder_name", "document_number", "nationality", "date_of_birth", "sex", "expiry_date")
LABELS = {
    "holder_name": r"HOLDER\s+NAME",
    "document_number": r"DOCUMENT\s+(?:NO|NUMBER)",
    "nationality": r"NATIONALITY",
    "date_of_birth": r"DATE\s+OF\s+BIRTH",
    "sex": r"SEX",
    "expiry_date": r"EXPIRY\s+DATE",
}


def _parse_tsv(tsv: str) -> tuple[str, dict[str, float], float | None]:
    lines: dict[tuple[str, str, str, str], list[tuple[str, float]]] = {}
    for row in csv.DictReader(StringIO(tsv), delimiter="\t"):
        text = (row.get("text") or "").strip()
        try:
            confidence = float(row.get("conf", "-1"))
        except ValueError:
            confidence = -1.0
        if not text or confidence < 0:
            continue
        key = tuple(row.get(part, "") for part in ("page_num", "block_num", "par_num", "line_num"))
        lines.setdefault(key, []).append((text, confidence))
    rendered: list[str] = []
    confidences: dict[str, float] = {}
    all_confidences: list[float] = []
    for words in lines.values():
        line = " ".join(word for word, _ in words)
        confidence = sum(value for _, value in words) / len(words)
        rendered.append(line)
        confidences[line] = round(confidence, 2)
        all_confidences.extend(value for _, value in words)
    overall = round(sum(all_confidences) / len(all_confidences), 2) if all_confidences else None
    return "\n".join(rendered), confidences, overall


def _tesseract(image: Image.Image, *, psm: int, whitelist: str | None = None) -> tuple[str, dict[str, float], float | None, str | None]:
    with tempfile.TemporaryDirectory() as directory:
        input_path = Path(directory) / "pixels.png"
        image.save(input_path, format="PNG")
        command = ["tesseract", str(input_path), "stdout", "--psm", str(psm), "-l", "eng", "tsv"]
        if whitelist:
            command[command.index("tsv"):command.index("tsv")] = ["-c", f"tessedit_char_whitelist={whitelist}"]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return "", {}, None, result.stderr.strip() or "Tesseract failed"
    text, line_confidences, overall = _parse_tsv(result.stdout)
    return text, line_confidences, overall, None


class LocalOcrAdapter:
    """Pixel-only local OCR. It has no filename, ID, manifest, or sidecar input."""

    def extract_text(self, specimen_bytes: bytes) -> dict[str, Any]:
        try:
            with Image.open(BytesIO(specimen_bytes)) as opened:
                opened.verify()
            with Image.open(BytesIO(specimen_bytes)) as opened:
                if opened.format not in {"PNG", "JPEG"}:
                    return {"visible_text": "", "mrz_text": "", "metadata": {"backend": "tesseract-5-local", "error": "Only decoded PNG/JPEG pixels are accepted."}}
                image = opened.convert("RGB")
                image_format = opened.format
        except (UnidentifiedImageError, OSError):
            return {"visible_text": "", "mrz_text": "", "metadata": {"backend": "tesseract-5-local", "error": "Input is not a valid PNG/JPEG image."}}

        width, height = image.size
        visible_crop = image.crop((int(width * 0.29), int(height * 0.21), int(width * 0.98), int(height * 0.69)))
        mrz_crop = image.crop((int(width * 0.035), int(height * 0.77), int(width * 0.97), int(height * 0.93)))
        visible_text, visible_lines, visible_confidence, visible_error = _tesseract(visible_crop, psm=6)
        mrz_text, mrz_lines, mrz_confidence, mrz_error = _tesseract(mrz_crop, psm=6, whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<")
        errors = [error for error in (visible_error, mrz_error) if error]
        return {
            "visible_text": visible_text,
            "mrz_text": mrz_text,
            "metadata": {
                "backend": "tesseract-5-local",
                "input_format": image_format,
                "image_size": [width, height],
                "visible_confidence": visible_confidence,
                "mrz_confidence": mrz_confidence,
                "visible_line_confidences": visible_lines,
                "mrz_line_confidences": mrz_lines,
                "error": "; ".join(errors) if errors else None,
            },
        }


def normalize_date(value: str) -> str | None:
    compact = re.sub(r"\s+", " ", value.strip().upper())
    for pattern in ("%d %b %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(compact, pattern).date().isoformat()
        except ValueError:
            continue
    return None


def normalize_visible_value(field: str, value: str) -> str | None:
    value = re.sub(r"\s+", " ", value.strip())
    if field in {"date_of_birth", "expiry_date"}:
        return normalize_date(value)
    if field in {"document_number", "nationality", "sex"}:
        return re.sub(r"\s+", "", value).upper()
    if field == "holder_name":
        return value.upper()
    return value or None


def extract_visible_fields(raw_text: str, line_confidences: dict[str, float] | None = None) -> tuple[dict[str, str], dict[str, str], dict[str, float]]:
    raw_fields: dict[str, str] = {}
    normalized_fields: dict[str, str] = {}
    field_confidences: dict[str, float] = {}
    for line in raw_text.splitlines():
        for field, label in LABELS.items():
            match = re.match(rf"^\s*{label}\s*[:\-]\s*(.+?)\s*$", line, flags=re.IGNORECASE)
            if not match:
                continue
            raw_value = match.group(1).strip()
            normalized = normalize_visible_value(field, raw_value)
            if raw_value:
                raw_fields[field] = raw_value
            if normalized:
                normalized_fields[field] = normalized
            if line_confidences and line in line_confidences:
                field_confidences[field] = line_confidences[line]
            break
    return raw_fields, normalized_fields, field_confidences


def extract_specimen(specimen_bytes: bytes) -> dict[str, Any]:
    ocr = LocalOcrAdapter().extract_text(specimen_bytes)
    metadata = ocr["metadata"]
    raw_fields, visible_fields, field_confidences = extract_visible_fields(ocr["visible_text"], metadata.get("visible_line_confidences"))
    missing_fields = [field for field in FIELDS if not visible_fields.get(field)]
    uncertain_fields = [field for field, confidence in field_confidences.items() if confidence < 50.0]
    return {
        "raw_ocr_text": "\n".join(part for part in (ocr["visible_text"], ocr["mrz_text"]) if part),
        "raw_visible_text": ocr["visible_text"],
        "raw_mrz_text": ocr["mrz_text"],
        "ocr_metadata": metadata,
        "raw_visible_fields": raw_fields,
        "visible_fields": visible_fields,
        "field_confidence": field_confidences,
        "missing_fields": missing_fields,
        "uncertain_fields": uncertain_fields,
    }
