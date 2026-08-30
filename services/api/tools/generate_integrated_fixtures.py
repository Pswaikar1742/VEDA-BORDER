#!/usr/bin/env python3
"""Create local, fictional integrated-workflow fixtures and detector-independent truth."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.mrz import check_digit
from tools.generate_synthetic_benchmark import FIELD_BOXES, PORTRAIT_BOX, credential, encode_image, font, render_credential


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "data" / "integrated_fixtures"
FACE_ROOT = ROOT / "services" / "api" / "assets" / "faces"


def _embed_portrait(image: Image.Image, face_path: Path, *, compression_cue: bool = False) -> Image.Image:
    result = image.copy()
    x1, y1, x2, y2 = PORTRAIT_BOX
    inset = (x1 + 9, y1 + 9, x2 - 9, y2 - 50)
    face = Image.open(face_path).convert("RGB")
    face = face.resize((inset[2] - inset[0], inset[3] - inset[1]), Image.Resampling.LANCZOS)
    if compression_cue:
        buffer = BytesIO()
        face.save(buffer, "JPEG", quality=46, subsampling=2)
        face = Image.open(BytesIO(buffer.getvalue())).convert("RGB")
    result.paste(face, inset)
    draw = ImageDraw.Draw(result)
    draw.rectangle((x1 + 9, y2 - 48, x2 - 9, y2 - 9), fill=(223, 232, 239))
    draw.text((x1 + 48, y2 - 42), "SYNTHETIC PORTRAIT", font=font("bold", 20), fill=(25, 38, 49))
    if compression_cue:
        draw.rectangle(inset, outline=(118, 34, 44), width=3)
    return result


def _expiry_payload(base: dict[str, str], expiry: str) -> dict[str, str]:
    result = dict(base)
    result["expiry_date"] = expiry
    value = expiry[2:].replace("-", "")
    line2 = result["mrz_line_2"]
    optional = line2[28:42]
    prefix = line2[:21] + value + check_digit(value) + optional + check_digit(optional)
    result["mrz_line_2"] = prefix + check_digit(prefix[:10] + prefix[13:20] + prefix[21:28] + prefix[28:43])
    return result


def _family_banner(image: Image.Image, family: str) -> Image.Image:
    result = image.copy()
    draw = ImageDraw.Draw(result)
    draw.rounded_rectangle((1120, 718, 1708, 775), radius=8, fill=(215, 230, 234), outline=(39, 61, 78), width=2)
    draw.text((1140, 731), family.replace("_", " "), font=font("bold", 22), fill=(18, 48, 61))
    return result


def _save(name: str, image: Image.Image, records: list[dict], scenario: str, family: str = "TRAVEL_DOCUMENT", **truth: object) -> None:
    path = OUTPUT / name
    data = encode_image(image)
    path.write_bytes(data)
    records.append({"filename": name, "scenario": scenario, "document_family": family, "sha256": hashlib.sha256(data).hexdigest(), **truth})


def generate() -> dict:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    ari, lio = FACE_ROOT / "ari_solen.png", FACE_ROOT / "lio_maren.png"
    records: list[dict] = []
    base = credential(20260830, 1)
    clean = _embed_portrait(render_credential(base), ari)
    _save("travel_clean.png", clean, records, "A_CLEAN_CONSISTENT", expected_outcome="LOW_RISK")

    dob = dict(base)
    dob["date_of_birth"] = "1991-06-18"
    _save("travel_dob_altered.png", _embed_portrait(render_credential(dob), ari), records, "B_DOB_ALTERED", affected_region=FIELD_BOXES["date_of_birth"], expected_gate="CRITICAL_CROSS_SOURCE_CONTRADICTION")

    portrait = _embed_portrait(render_credential(base), lio, compression_cue=True)
    _save("travel_portrait_replaced.png", portrait, records, "C_PORTRAIT_REPLACED", affected_region=PORTRAIT_BOX, expected_biometric="MISMATCH")

    expired = _expiry_payload(base, "2024-02-21")
    _save("travel_expired.png", _embed_portrait(render_credential(expired), ari), records, "D_EXPIRED", expected_gate="EXPIRED_DOCUMENT")

    blacklisted = credential(20260830, 4)
    _save("travel_blacklisted.png", _embed_portrait(render_credential(blacklisted), ari), records, "E_LOCAL_WATCHLIST_HIT", expected_intelligence="DOCUMENT_BLACKLISTED")

    low_resolution = clean.resize((540, 330), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(2.4))
    _save("travel_poor_capture.png", low_resolution, records, "I_POOR_CAPTURE", expected_quality="FAIL")

    for family, filename in (("VISA_OR_PERMIT", "visa_or_permit.png"), ("NATIONAL_ID", "national_id.png"), ("DRIVING_LICENCE", "driving_licence.png")):
        _save(filename, _family_banner(clean, family), records, f"FAMILY_{family}", family=family, expected_mrz="NOT_APPLICABLE")

    ari_face = Image.open(ari).convert("RGB")
    lio_face = Image.open(lio).convert("RGB")
    _save("ari_selfie.png", ari_face, records, "SYNTHETIC_SELFIE_MATCH", family="FACE_IMAGE")
    ari_variant = ImageEnhance.Brightness(ari_face.rotate(1.4, resample=Image.Resampling.BICUBIC, fillcolor=(215, 215, 215))).enhance(0.94)
    _save("ari_selfie_variant.png", ari_variant, records, "SYNTHETIC_SELFIE_SAME_IDENTITY", family="FACE_IMAGE")
    _save("lio_selfie.png", lio_face, records, "SYNTHETIC_SELFIE_MISMATCH", family="FACE_IMAGE")

    manifest = {
        "dataset_id": "veda-integrated-research-prototype-golden-v1",
        "generation_seed": 20260830,
        "safety_boundary": "All identities and credentials are fictional/synthetic. No real document design or government connection.",
        "runtime_truth_boundary": "Runtime accepts image bytes only and cannot read this manifest.",
        "records": records,
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


if __name__ == "__main__":
    print(json.dumps({"records": len(generate()["records"]), "output": str(OUTPUT)}))
