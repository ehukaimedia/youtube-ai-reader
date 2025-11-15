from __future__ import annotations

import logging
import re
import shutil
from typing import Iterable, List


logger = logging.getLogger(__name__)


def extract_video_id(url: str) -> str:
    match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    if not match:
        raise ValueError("Unable to extract video ID")
    return match.group(1)


def ensure_commands_available(commands: Iterable[str]) -> None:
    missing: List[str] = [cmd for cmd in commands if shutil.which(cmd) is None]
    if missing:
        raise RuntimeError(f"Missing required system binaries: {', '.join(missing)}")
    logger.debug("Verified binaries present: %s", ", ".join(commands))
