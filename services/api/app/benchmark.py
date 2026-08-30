from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SpecimenKind(str, Enum):
    CLEAN = "CLEAN"
    CONTROLLED_VARIANT = "CONTROLLED_VARIANT"
    CAPTURE_DEGRADATION = "CAPTURE_DEGRADATION"


class TransformationType(str, Enum):
    NAME_SUBSTITUTION = "name_substitution"
    BIRTH_DATE_SUBSTITUTION = "birth_date_substitution"
    EXPIRY_DATE_SUBSTITUTION = "expiry_date_substitution"
    PORTRAIT_REGION_REPLACEMENT = "portrait_region_replacement"


class CaptureDegradationType(str, Enum):
    MILD_ROTATION = "mild_rotation"
    MILD_PERSPECTIVE = "mild_perspective"
    MILD_BLUR = "mild_blur"
    JPEG_RECOMPRESSION = "jpeg_recompression"
    BRIGHTNESS_VARIATION = "brightness_variation"


class Transformation(BaseModel):
    type: TransformationType | CaptureDegradationType
    affected_field_or_region: str
    pre_value: str | None = None
    post_value: str | None = None
    bounding_box: tuple[int, int, int, int]
    segmentation_mask: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class BenchmarkRecord(BaseModel):
    specimen_id: str
    parent_specimen_id: str | None
    relative_path: str
    format: str
    kind: SpecimenKind
    credential_family: str
    issuer_label: str
    contains_real_pii: bool = False
    transformation_derived_ground_truth: bool = True
    transformations: list[Transformation] = Field(default_factory=list)
    sha256: str
    size_bytes: int
    expected_evidence_condition: dict[str, Any]
    generation_seed: int
    expected_contradiction: dict[str, Any]
    expected_visible_fields: dict[str, str] = Field(default_factory=dict)
    expected_visible_raw_fields: dict[str, str] = Field(default_factory=dict)
    expected_mrz_fields: dict[str, str] = Field(default_factory=dict)


class BenchmarkManifest(BaseModel):
    schema_version: str = "veda.synthetic-image-benchmark.v2"
    dataset_id: str
    seed: int
    description: str
    safety_boundary: str
    records: list[BenchmarkRecord]
