from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    fast_router_api_key: str = ""
    fast_router_base_url: str = ""
    fast_router_model: str = ""
    fast_router_enabled: bool = False
    fast_router_max_requests: int = 0
    fast_router_max_spend_usd: float = 0.0
    mock_border_intelligence_enabled: bool = True
    threat_intelligence_mandatory: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)


settings = Settings()
