from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "WellGuard AI"
    api_prefix: str = ""
    default_oil_price: float = 70.0
    default_decline_threshold: float = 0.15
    database_url: str = "sqlite:///./wellguard.db"
    data_dir: Path = Path(__file__).resolve().parents[3] / "data"
    optional_openai_api_key: Optional[str] = None

    class Config:
        env_file = ".env"
        env_prefix = "WELLGUARD_"


@lru_cache
def get_settings() -> Settings:
    return Settings()
