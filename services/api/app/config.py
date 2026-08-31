from pathlib import Path
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _repo_root() -> Path:
    current = Path(__file__).resolve().parent
    for parent in [current, *current.parents]:
        if (parent / "services" / "api").is_dir() and (parent / "data").is_dir():
            return parent
    return Path.cwd()


REPO_ROOT = _repo_root()


def resolve_repo_path(path_str: str) -> str:
    p = Path(path_str)
    if p.is_absolute() or p.exists():
        return str(p)
    candidate = REPO_ROOT / p
    if candidate.exists() or candidate.parent.exists():
        return str(candidate)
    return str(p)


class Settings(BaseSettings):
    fast_router_api_key: str = Field(default="", validation_alias=AliasChoices("FASTROUTER_API_KEY", "fast_router_api_key", "FAST_ROUTER_API_KEY"))
    fast_router_base_url: str = Field(default="https://api.fastrouter.ai/api/v1", validation_alias=AliasChoices("FASTROUTER_BASE_URL", "fast_router_base_url", "FAST_ROUTER_BASE_URL"))
    fast_router_model: str = Field(default="fastrouter/auto", validation_alias=AliasChoices("FASTROUTER_MODEL", "fast_router_model", "FAST_ROUTER_MODEL"))
    fast_router_enabled: bool = Field(default=False, validation_alias=AliasChoices("FASTROUTER_ENABLED", "fast_router_enabled", "FAST_ROUTER_ENABLED"))
    fast_router_max_requests: int = Field(default=0, validation_alias=AliasChoices("FASTROUTER_MAX_REQUESTS", "fast_router_max_requests", "FAST_ROUTER_MAX_REQUESTS"))
    fast_router_max_spend_usd: float = Field(default=0.0, validation_alias=AliasChoices("FASTROUTER_MAX_SPEND_USD", "fast_router_max_spend_usd", "FAST_ROUTER_MAX_SPEND_USD"))
    mock_border_intelligence_enabled: bool = True
    threat_intelligence_mandatory: bool = True
    case_database_path: str = "data/runtime/veda_border.db"
    face_detector_model: str = "services/api/assets/models/face_detection_yunet_2023mar.onnx"
    face_recognizer_model: str = "services/api/assets/models/face_recognition_sface_2021dec.onnx"
    face_match_threshold: float = 0.55
    identity_linkage_threshold: float = 0.50
    visual_forensics_enabled: bool = True
    biometrics_enabled: bool = True
    minimum_image_width: int = 700
    minimum_image_height: int = 440

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)


settings = Settings()
