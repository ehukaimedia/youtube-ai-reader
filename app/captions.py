from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

import requests
from PIL import Image

try:
    import pytesseract
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None

from .config import settings


def extract_ocr_text(image_path: Path) -> Optional[str]:
    """Returns textual content from a frame using Tesseract when available."""

    if pytesseract is None or not settings.enable_ocr:
        return None
    try:
        with Image.open(image_path) as img:
            text = pytesseract.image_to_string(img)
        cleaned = text.strip()
        return cleaned or None
    except Exception:
        return None


def generate_caption(image_path: Path) -> Optional[str]:
    """Generates a natural-language caption via Ollama when enabled."""

    if not settings.ollama_model:
        return None
    try:
        with image_path.open("rb") as buf:
            encoded = base64.b64encode(buf.read()).decode("utf-8")
        payload = {
            "model": settings.ollama_model,
            "prompt": (
                "You are analysing a frame extracted from a trading screencast. "
                "Return one concise sentence describing the key on-screen content, "
                "including text overlays or chart state if visible."
            ),
            "images": [encoded],
            "stream": False,
            "options": {"temperature": 0.1},
        }
        response = requests.post(f"{settings.ollama_url}/api/generate", timeout=60, json=payload)
        response.raise_for_status()
        data = response.json()
        caption = (data.get("response") or "").strip()
        return caption or None
    except Exception:
        return None
