"""Settings, read from environment variables prefixed HIGHGROUND_ or from a .env file."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_project_root() -> Path:
    """The folder holding content/, data/, templates/ and static/."""
    cwd = Path.cwd()
    if (cwd / "content").is_dir():
        return cwd
    return Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HIGHGROUND_", env_file=".env", extra="ignore")

    project_root: Path = _default_project_root()

    # Vision-language model (vLLM on the GB10, OpenAI-compatible API).
    vlm_enabled: bool = True
    vlm_base_url: str = "http://localhost:8000/v1"
    vlm_model: str = "Qwen/Qwen3-VL-8B-Instruct"
    vlm_api_key: str = "NONE"
    vlm_timeout_s: float = 20.0

    # Live public feeds.
    live_data_enabled: bool = True
    live_timeout_s: float = 8.0
    contact_email: str = "team@example.org"
    nws_base_url: str = "https://api.weather.gov"
    usgs_base_url: str = "https://api.waterdata.usgs.gov/ogcapi/v0"

    # Data.
    images_dir: Path | None = None
    max_snap_km: float = 1.0

    @field_validator("images_dir", mode="before")
    @classmethod
    def _blank_is_none(cls, value: object) -> object:
        return None if value in ("", None) else value

    @property
    def content_dir(self) -> Path:
        return self.project_root / "content"

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def templates_dir(self) -> Path:
        return self.project_root / "templates"

    @property
    def static_dir(self) -> Path:
        return self.project_root / "static"

    @property
    def sites_csv(self) -> Path:
        return self.data_dir / "hill_country_sites.csv"

    @property
    def replay_dir(self) -> Path:
        return self.data_dir / "replay"


@lru_cache
def get_settings() -> Settings:
    return Settings()
