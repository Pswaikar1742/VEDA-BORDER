#!/usr/bin/env python3
"""Render deterministic, unmistakably fictional credential images and truth."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import date
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.benchmark import BenchmarkManifest, BenchmarkRecord, CaptureDegradationType, SpecimenKind, Transformation, TransformationType
from app.mrz import check_digit


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = ROOT / "data" / "synthetic_benchmark"
FAMILY = "VEDA_FICTIONAL_CREDENTIAL"
ISSUER = "NORTHSTAR DEMO AUTHORITY - FICTIONAL STATE"
CANVAS = (1800, 1100)
PORTRAIT_BOX = (80, 280, 500, 745)
FIELD_BOXES = {
    "holder_name": (560, 250, 1710, 318), "document_number": (560, 330, 1710, 398),
    "nationality": (560, 410, 1710, 478), "date_of_birth": (560, 490, 1710, 558),
    "sex": (560, 570, 1710, 638), "expiry_date": (560, 650, 1710, 718),
}
FULL_BOX = (0, 0, CANVAS[0], CANVAS[1])
FONT_CANDIDATES = {
    "sans": ("/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    "bold": ("/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    "mono": ("/usr/share/fonts/google-noto/NotoSansMono-Regular.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
}


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES[kind]:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size=size)
    raise RuntimeError(f"Required local {kind} font was not found")


def display_date(value: str) -> str:
    return date.fromisoformat(value).strftime("%d %b %Y").upper()


def credential(seed: int, index: int) -> dict[str, str]:
    people = [
        ("ARI SOLEN", "1994-03-17", "2031-02-21", "X"),
        ("MIRA QUEN", "1988-09-22", "2032-03-22", "F"),
        ("TAVI ORIN", "2001-01-08", "2033-04-23", "M"),
        ("NERA VALE", "1996-12-04", "2034-05-24", "X"),
    ]
    holder_name, birth_date, expiry_date, sex = people[index - 1]
    document_number = "VDA" + str(index) * 6
    dob, expiry = birth_date[2:].replace("-", ""), expiry_date[2:].replace("-", "")
    given, surname = holder_name.split(" ", 1)
    line1 = f"X<NSL{surname}<<{given}".replace(" ", "<").ljust(44, "<")[:44]
    optional = f"TEST{chr(64 + index)}".ljust(14, "<")
    line2_prefix = document_number + check_digit(document_number) + "NSL" + dob + check_digit(dob) + sex + expiry + check_digit(expiry) + optional + check_digit(optional)
    line2 = line2_prefix + check_digit(line2_prefix[:10] + line2_prefix[13:20] + line2_prefix[21:28] + line2_prefix[28:43])
    return {"holder_name": holder_name, "document_number": document_number, "nationality": "NSL", "date_of_birth": birth_date, "sex": sex, "expiry_date": expiry_date, "mrz_line_1": line1, "mrz_line_2": line2, "portrait_token": f"PORTRAIT-{seed}-{index:02d}"}


def raw_visible_fields(payload: dict[str, str]) -> dict[str, str]:
    return {"holder_name": payload["holder_name"], "document_number": payload["document_number"], "nationality": payload["nationality"], "date_of_birth": display_date(payload["date_of_birth"]), "sex": payload["sex"], "expiry_date": display_date(payload["expiry_date"])}


def draw_portrait(draw: ImageDraw.ImageDraw, token: str) -> None:
    x1, y1, x2, y2 = PORTRAIT_BOX
    variant = int(hashlib.sha256(token.encode()).hexdigest()[:2], 16)
    background, accent = (223, 232 + variant % 12, 239), (46 + variant % 35, 82, 120 + variant % 50)
    draw.rounded_rectangle(PORTRAIT_BOX, radius=24, fill=background, outline=(39, 61, 78), width=5)
    draw.ellipse((x1 + 118, y1 + 55, x1 + 302, y1 + 239), fill=(247, 197, 158), outline=accent, width=5)
    draw.polygon([(x1 + 120, y1 + 135), (x1 + 205, y1 + 45), (x1 + 305, y1 + 137)], fill=accent)
    draw.rounded_rectangle((x1 + 70, y1 + 240, x2 - 70, y2 - 55), radius=90, fill=accent)
    draw.text((x1 + 88, y2 - 48), "FICTIONAL PORTRAIT", font=font("bold", 22), fill=(25, 38, 49))


def render_credential(payload: dict[str, str]) -> Image.Image:
    image = Image.new("RGB", CANVAS, (247, 250, 251))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((28, 28, 1772, 1072), radius=34, fill=(247, 250, 251), outline=(21, 69, 92), width=8)
    draw.rectangle((32, 32, 1768, 205), fill=(15, 65, 88))
    draw.text((70, 55), "VEDA-BORDER SYNTHETIC DEMO CREDENTIAL", font=font("bold", 48), fill=(255, 255, 255))
    draw.text((70, 122), "NOT A REAL TRAVEL DOCUMENT", font=font("bold", 38), fill=(255, 216, 90))
    draw.text((70, 174), ISSUER, font=font("sans", 23), fill=(225, 242, 247))
    draw_portrait(draw, payload["portrait_token"])
    labels = {"holder_name": "HOLDER NAME", "document_number": "DOCUMENT NO", "nationality": "NATIONALITY", "date_of_birth": "DATE OF BIRTH", "sex": "SEX", "expiry_date": "EXPIRY DATE"}
    raw = raw_visible_fields(payload)
    for field_name, box in FIELD_BOXES.items():
        x1, y1, _, _ = box
        draw.rounded_rectangle(box, radius=10, fill=(255, 255, 255), outline=(166, 185, 193), width=2)
        draw.text((x1 + 18, y1 + 14), f"{labels[field_name]}: {raw[field_name]}", font=font("bold", 34), fill=(18, 32, 42))
    draw.rectangle((62, 790, 1738, 1040), fill=(232, 239, 241), outline=(39, 61, 78), width=4)
    draw.text((90, 808), "MACHINE READABLE ZONE - FICTIONAL", font=font("bold", 25), fill=(25, 45, 56))
    draw.text((90, 868), payload["mrz_line_1"], font=font("mono", 37), fill=(0, 0, 0), stroke_width=1)
    draw.text((90, 934), payload["mrz_line_2"], font=font("mono", 37), fill=(0, 0, 0), stroke_width=1)
    draw.text((75, 1048), "DEMO DATA / FICTIONAL STATE / NO GOVERNMENT CONNECTION", font=font("bold", 20), fill=(120, 38, 38))
    return image


def encode_image(image: Image.Image, image_format: str = "PNG") -> bytes:
    buffer = BytesIO()
    if image_format == "JPEG":
        image.save(buffer, format="JPEG", quality=84, optimize=False, progressive=False, subsampling=0)
    else:
        image.save(buffer, format="PNG", compress_level=9, optimize=False)
    return buffer.getvalue()


def write_specimen(out_dir: Path, specimen_id: str, image: Image.Image, image_format: str = "PNG") -> tuple[str, int, str]:
    suffix = ".jpg" if image_format == "JPEG" else ".png"
    path = out_dir / "specimens" / f"{specimen_id}{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = encode_image(image, image_format)
    path.write_bytes(data)
    return str(path.relative_to(out_dir)), len(data), sha256(data)


def expected_mrz(payload: dict[str, str]) -> dict[str, str]:
    return {key: payload[key] for key in ("holder_name", "document_number", "nationality", "date_of_birth", "sex", "expiry_date")}


def build_record(out_dir: Path, specimen_id: str, payload: dict[str, str], image: Image.Image, *, seed: int, kind: SpecimenKind, parent: str | None, transformations: list[Transformation], expected: dict[str, object], contradiction: dict[str, object], mrz_payload: dict[str, str] | None = None, image_format: str = "PNG") -> BenchmarkRecord:
    relative_path, size, digest = write_specimen(out_dir, specimen_id, image, image_format)
    return BenchmarkRecord(
        specimen_id=specimen_id, parent_specimen_id=parent, relative_path=relative_path, format=image_format,
        kind=kind, credential_family=FAMILY, issuer_label=ISSUER, transformations=transformations,
        sha256=digest, size_bytes=size, expected_evidence_condition=expected, generation_seed=seed,
        expected_contradiction=contradiction,
        expected_visible_fields={key: payload[key] for key in ("holder_name", "document_number", "nationality", "date_of_birth", "sex", "expiry_date")},
        expected_visible_raw_fields=raw_visible_fields(payload), expected_mrz_fields=expected_mrz(mrz_payload or payload),
    )


def apply_capture_degradation(image: Image.Image, degradation: CaptureDegradationType) -> tuple[Image.Image, str, dict[str, object]]:
    if degradation == CaptureDegradationType.MILD_ROTATION:
        return image.rotate(1.25, resample=Image.Resampling.BICUBIC, fillcolor=(247, 250, 251)), "PNG", {"angle_degrees": 1.25}
    if degradation == CaptureDegradationType.MILD_PERSPECTIVE:
        quad = (12, 8, 18, image.height - 2, image.width - 8, image.height - 12, image.width - 18, 0)
        return image.transform(image.size, Image.Transform.QUAD, quad, resample=Image.Resampling.BICUBIC, fillcolor=(247, 250, 251)), "PNG", {"source_quadrilateral": quad}
    if degradation == CaptureDegradationType.MILD_BLUR:
        return image.filter(ImageFilter.GaussianBlur(radius=0.55)), "PNG", {"gaussian_radius": 0.55}
    if degradation == CaptureDegradationType.JPEG_RECOMPRESSION:
        return image, "JPEG", {"jpeg_quality": 84, "subsampling": 0}
    if degradation == CaptureDegradationType.BRIGHTNESS_VARIATION:
        return ImageEnhance.Brightness(image).enhance(0.88), "PNG", {"brightness_factor": 0.88}
    raise ValueError(f"Unsupported capture degradation: {degradation}")


def generate(output: Path, seed: int = 20260829) -> BenchmarkManifest:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    records: list[BenchmarkRecord] = []
    clean_payloads: dict[str, dict[str, str]] = {}
    replacement_names = ("LIO MAREN", "SORA KEST", "ELI NOVA", "RIN TAL")
    for index in range(1, 5):
        clean_id = f"clean-{index:03d}"
        base = credential(seed, index)
        clean_payloads[clean_id] = base
        records.append(build_record(output, clean_id, base, render_credential(base), seed=seed, kind=SpecimenKind.CLEAN, parent=None, transformations=[], expected={"condition": "CONSISTENT", "basis": "untransformed rendered image"}, contradiction={"expected": False, "field": None}))
        variants = (
            (TransformationType.NAME_SUBSTITUTION, "holder_name", replacement_names[index - 1]),
            (TransformationType.BIRTH_DATE_SUBSTITUTION, "date_of_birth", f"19{90 + index}-06-18"),
            (TransformationType.EXPIRY_DATE_SUBSTITUTION, "expiry_date", f"202{index}-02-21"),
            (TransformationType.PORTRAIT_REGION_REPLACEMENT, "portrait_region", f"REPLACED-PORTRAIT-{index:02d}"),
        )
        for variant_number, (transformation_type, field_name, replacement) in enumerate(variants, start=1):
            changed = dict(base)
            payload_key = "portrait_token" if field_name == "portrait_region" else field_name
            original = changed[payload_key]
            changed[payload_key] = replacement
            contradiction_field = None if field_name == "portrait_region" else field_name
            bbox = PORTRAIT_BOX if field_name == "portrait_region" else FIELD_BOXES[field_name]
            transformation = Transformation(type=transformation_type, affected_field_or_region=field_name, pre_value=original, post_value=replacement, bounding_box=bbox, parameters={"method": "deterministic_region_only_replacement", "seed": seed, "variant_number": variant_number})
            records.append(build_record(
                output, f"variant-{index:03d}-{variant_number:02d}", changed, render_credential(changed), seed=seed,
                kind=SpecimenKind.CONTROLLED_VARIANT, parent=clean_id, transformations=[transformation],
                expected={"condition": "CONTROLLED_VISIBLE_REGION_CHANGE", "affected_field_or_region": field_name, "detector_must_be_independent": True},
                contradiction={"expected": contradiction_field is not None, "field": contradiction_field, "viz_value": changed.get(payload_key), "mrz_value": base.get(payload_key) if contradiction_field else None}, mrz_payload=base,
            ))

    capture_parent, capture_payload = "clean-001", clean_payloads["clean-001"]
    capture_image = render_credential(capture_payload)
    for number, degradation in enumerate(CaptureDegradationType, start=1):
        degraded, image_format, parameters = apply_capture_degradation(capture_image, degradation)
        transformation = Transformation(type=degradation, affected_field_or_region="full_image_capture_condition", pre_value="clean_render", post_value=degradation.value, bounding_box=FULL_BOX, parameters={"identity_truth_changed": False, "seed": seed, **parameters})
        records.append(build_record(
            output, f"capture-001-{number:02d}", capture_payload, degraded, seed=seed,
            kind=SpecimenKind.CAPTURE_DEGRADATION, parent=capture_parent, transformations=[transformation],
            expected={"condition": "CAPTURE_CONDITION_ONLY", "identity_truth_changed": False}, contradiction={"expected": False, "field": None}, image_format=image_format,
        ))

    manifest = BenchmarkManifest(dataset_id="veda-fictional-credential-image-benchmark-v2", seed=seed, description="Rendered fictional credential images, visible-region-only controlled variants, and small capture-condition variants. Labels describe programmed transformations only.", safety_boundary="No real identity data, real document layout, government emblem, seal, national symbol, operational identifier, fraud label, or authenticity label.", records=records)
    (output / "manifest.json").write_bytes(canonical_json(manifest.model_dump(mode="json")))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=20260829)
    args = parser.parse_args()
    manifest = generate(args.output, args.seed)
    summary = {kind.value.lower(): sum(record.kind == kind for record in manifest.records) for kind in SpecimenKind}
    print(json.dumps({"output": str(args.output), "seed": args.seed, "records": len(manifest.records), **summary}, sort_keys=True))


if __name__ == "__main__":
    main()
