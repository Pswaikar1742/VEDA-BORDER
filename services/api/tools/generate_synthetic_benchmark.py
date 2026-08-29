#!/usr/bin/env python3
"""Generate fictional credential specimens and transformation-derived truth."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.benchmark import (
    BenchmarkManifest,
    BenchmarkRecord,
    SpecimenKind,
    Transformation,
    TransformationType,
)
from app.mrz import check_digit


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = ROOT / "data" / "synthetic_benchmark"
FAMILY = "FANTASY_CIVIC_CREDENTIAL"
ISSUER = "Northstar Civic Lab (fictional)"


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def render_visible_text(payload: dict[str, str]) -> str:
    return "\n".join([
        "VEDA FANTASY CIVIC CREDENTIAL", f"Holder Name: {payload['holder_name']}",
        f"Credential Reference: {payload['credential_ref']}", f"Nationality: {payload['nationality']}",
        f"Date of Birth: {payload['birth_date']}", f"Valid Until: {payload['valid_until']}", "Sex: X", "MRZ:",
        payload["mrz_line_1"], payload["mrz_line_2"],
    ])


def credential(seed: int, index: int) -> dict[str, str]:
    rng = random.Random(seed * 1000 + index)
    names = [("Ari Solen", "1994-03-17"), ("Mira Quen", "1988-09-22"), ("Tavi Orin", "2001-01-08"), ("Nera Vale", "1996-12-04")]
    name, birth_date = names[index - 1]
    mrz_document_number = f"X{index:02d}{rng.randrange(100000, 999999)}"
    dob = birth_date[2:].replace("-", "")
    expiry_date = f"203{index}-0{index + 1}-2{index}"
    expiry = expiry_date[2:].replace("-", "")
    given, surname = name.split()
    line1 = f"X<NSL{surname.upper()}<<{given.upper()}".replace(" ", "<").ljust(44, "<")[:44]
    optional = "<" * 14
    line2_prefix = mrz_document_number + check_digit(mrz_document_number) + "NSL" + dob + check_digit(dob) + "X" + expiry + check_digit(expiry) + optional + check_digit(optional)
    mrz_line2 = line2_prefix + check_digit(line2_prefix[:10] + line2_prefix[13:20] + line2_prefix[21:28] + line2_prefix[28:43])
    credential_ref = f"FIC-{index:02d}-{rng.randrange(1000, 9999)}"
    payload = {
        "credential_family": FAMILY,
        "credential_ref": credential_ref,
        "nationality": "NSL",
        "issuer_label": ISSUER,
        "holder_name": name,
        "birth_date": birth_date,
        "valid_until": f"203{index}-0{index + 1}-2{index}",
        "portrait_region_token": f"PORTRAIT-TOKEN-{index:02d}",
        "mrz_document_number": mrz_document_number,
        "mrz_line_1": line1,
        "mrz_line_2": mrz_line2,
        "visible_text": "",
        "design_note": "Fantasy data artifact; not issued by a government and not a real identity document.",
    }
    payload["visible_text"] = render_visible_text(payload)
    return payload


def write_specimen(out_dir: Path, specimen_id: str, payload: dict[str, str]) -> tuple[str, int, str]:
    path = out_dir / "specimens" / f"{specimen_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_json(payload)
    path.write_bytes(data)
    return str(path.relative_to(out_dir)), len(data), sha256(data)


def build_record(out_dir: Path, specimen_id: str, payload: dict[str, str], *, parent: str | None, transformations: list[Transformation], expected: dict[str, object]) -> BenchmarkRecord:
    relative_path, size, digest = write_specimen(out_dir, specimen_id, payload)
    return BenchmarkRecord(
        specimen_id=specimen_id,
        parent_specimen_id=parent,
        relative_path=relative_path,
        format="JSON",
        kind=SpecimenKind.CLEAN if parent is None else SpecimenKind.CONTROLLED_VARIANT,
        credential_family=FAMILY,
        issuer_label=ISSUER,
        transformations=transformations,
        sha256=digest,
        size_bytes=size,
        expected_evidence_condition=expected,
        expected_visible_fields={"holder_name": payload["holder_name"], "document_number": payload["credential_ref"], "nationality": payload["nationality"], "date_of_birth": payload["birth_date"], "expiry_date": payload["valid_until"], "sex": "X"},
        expected_mrz_fields={"document_number": payload["mrz_document_number"], "nationality": payload["nationality"], "date_of_birth": payload["birth_date"], "expiry_date": payload["valid_until"], "sex": "X"},
    )


def generate(output: Path, seed: int = 20260829) -> BenchmarkManifest:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    records: list[BenchmarkRecord] = []
    substitutions = {
        TransformationType.NAME_SUBSTITUTION: ("holder_name", "Ari Solen", "Lio Maren"),
        TransformationType.BIRTH_DATE_SUBSTITUTION: ("birth_date", "1994-03-17", "1994-03-18"),
        TransformationType.EXPIRY_DATE_SUBSTITUTION: ("valid_until", "2031-02-21", "2021-02-21"),
        TransformationType.PORTRAIT_REGION_REPLACEMENT: ("portrait_region", "PORTRAIT-TOKEN-01", "PORTRAIT-TOKEN-01-REPLACED"),
    }
    for index in range(1, 5):
        clean_id = f"clean-{index:03d}"
        base = credential(seed, index)
        records.append(build_record(output, clean_id, base, parent=None, transformations=[], expected={"condition": "CONSISTENT", "basis": "untransformed canonical specimen"}))
        for variant_number, (kind, (field, pre, post)) in enumerate(substitutions.items(), start=1):
            variant_id = f"variant-{index:03d}-{variant_number:02d}"
            changed = dict(base)
            if field == "portrait_region":
                changed["portrait_region_token"] = post
            else:
                changed[field] = post if not (index > 1 and kind == TransformationType.NAME_SUBSTITUTION) else f"{post} {index}"
            actual_post = changed.get(field, changed.get("portrait_region_token", post))
            actual_pre = base.get(field, base.get("portrait_region_token", pre))
            changed["visible_text"] = render_visible_text(changed)
            transformation = Transformation(type=kind, affected_field_or_region=field, pre_value=actual_pre, post_value=actual_post, parameters={"method": "deterministic_single_field_replacement", "seed": seed, "variant_number": variant_number})
            record = build_record(output, variant_id, changed, parent=clean_id, transformations=[transformation], expected={"condition": "CONTROLLED_MISMATCH", "affected_field_or_region": field, "detector_must_be_independent": True})
            record.expected_mrz_fields = {"document_number": base["mrz_document_number"], "nationality": base["nationality"], "date_of_birth": base["birth_date"], "expiry_date": base["valid_until"], "sex": "X"}
            records.append(record)
    manifest = BenchmarkManifest(dataset_id="veda-fantasy-credential-benchmark-v1", seed=seed, description="Deterministic fictional credentials and controlled integrity variants. Labels describe programmed transformations only, never fraud or authenticity.", safety_boundary="No real identity data, passport/visa/Aadhaar design, government emblem, operational identifier scheme, OCR, detector, biometric, scoring, or external provider.", records=records)
    (output / "manifest.json").write_bytes(canonical_json(manifest.model_dump(mode="json")))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=20260829)
    args = parser.parse_args()
    manifest = generate(args.output, args.seed)
    print(json.dumps({"output": str(args.output), "seed": args.seed, "records": len(manifest.records), "clean": sum(r.kind == SpecimenKind.CLEAN for r in manifest.records), "variants": sum(r.kind == SpecimenKind.CONTROLLED_VARIANT for r in manifest.records)}, sort_keys=True))


if __name__ == "__main__":
    main()
