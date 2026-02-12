from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Indian Trend Predictor"
    env: str = Field(default="dev")
    log_level: str = Field(default="INFO")

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@db:5432/indian_market_ai"
    )

    primary_data_provider: str = Field(default="nse")
    backup_data_provider: str = Field(default="yahoo")

    model_registry_path: str = Field(default="/models")
    confidence_floor: float = Field(default=0.35)
    validator_disagreement_threshold: float = Field(default=0.22)

    timezone: str = Field(default="Asia/Kolkata")


@lru_cache
def get_settings() -> Settings:
    return Settings()
