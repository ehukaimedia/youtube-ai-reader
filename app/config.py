from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the service."""

    data_root: Path = Field(default=Path(__file__).resolve().parents[1] / "data" / "jobs")
    frame_scene_threshold: float = Field(default=0.28, ge=0.0, le=1.0)
    download_retries: int = Field(default=3, ge=1, le=5)
    download_retry_backoff_sec: float = Field(default=2.0, ge=0.1, le=30.0)
    download_timeout_sec: Optional[int] = Field(default=None, ge=30)
    log_level: str = Field(default="INFO")

    whisper_model: str = Field(default="small")
    whisper_device: str = Field(default="cpu")
    whisper_compute_type: str = Field(default="int8")

    enable_ocr: bool = Field(default=True)
    ollama_model: Optional[str] = Field(default=None)
    ollama_url: str = Field(default="http://localhost:11434")

    class Config:
        env_file = ".env"
        env_prefix = "YTAI_"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
