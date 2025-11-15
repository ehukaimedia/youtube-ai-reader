from __future__ import annotations

import shutil
from typing import Dict

import requests

from .config import settings


DEPENDENCIES = ["ffmpeg", "yt-dlp"]


def dependency_snapshot() -> Dict[str, bool]:
    snapshot = {name: shutil.which(name) is not None for name in DEPENDENCIES}
    snapshot["tesseract"] = shutil.which("tesseract") is not None and settings.enable_ocr
    snapshot["ollama"] = _ollama_healthy() if settings.ollama_model else False
    return snapshot


def _ollama_healthy() -> bool:
    try:
        response = requests.get(f"{settings.ollama_url}/api/tags", timeout=2)
        response.raise_for_status()
        return True
    except Exception:
        return False
