from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any


DEFAULT_DATA_ROOT = Path(os.environ.get("DATA_ROOT", Path(__file__).resolve().parents[1] / "data" / "jobs"))


def job_dir(job_id: str, data_root: Path = DEFAULT_DATA_ROOT) -> Path:
    path = data_root / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def package_directory(job_directory: Path) -> Path:
    base_name = job_directory / "bundle"
    archive_path = base_name.with_suffix(".zip")
    if archive_path.exists():
        archive_path.unlink()
    shutil.make_archive(str(base_name), "zip", root_dir=job_directory)
    return archive_path
