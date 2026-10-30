"""Core configuration for AquaShift backend."""

from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "models"


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    app_name: str = "AquaShift"
    debug: bool = False

    # Region config
    region_name: str = "Punjab-Haryana Belt"
    default_land_ha: float = 1000.0
    default_water_budget_m3: float = 8_000_000.0

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    model_config = {"env_file": str(ROOT_DIR / ".env"), "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
