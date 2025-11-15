from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from .schemas import JobCreateRequest, JobResponse, JobStatus, Manifest


@dataclass
class JobRecord:
    id: str
    config: JobCreateRequest
    status: JobStatus = JobStatus.pending
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None
    manifest: Optional[Manifest] = None
    package_path: Optional[Path] = None

    def to_response(self) -> JobResponse:
        return JobResponse(
            id=self.id,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            error=self.error,
            manifest=self.manifest,
        )


class JobStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobRecord] = {}
        self._lock = threading.Lock()

    def create_job(self, config: JobCreateRequest) -> JobRecord:
        job_id = uuid.uuid4().hex
        record = JobRecord(id=job_id, config=config)
        with self._lock:
            self._jobs[job_id] = record
        return record

    def _require(self, job_id: str) -> JobRecord:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise KeyError(f"Job {job_id} not found") from exc

    def get(self, job_id: str) -> JobRecord:
        with self._lock:
            return self._require(job_id)

    def mark_in_progress(self, job_id: str) -> None:
        with self._lock:
            record = self._require(job_id)
            record.status = JobStatus.in_progress
            record.updated_at = datetime.now(timezone.utc)

    def mark_complete(self, job_id: str, manifest: Manifest, package_path: Path) -> None:
        with self._lock:
            record = self._require(job_id)
            record.status = JobStatus.complete
            record.updated_at = datetime.now(timezone.utc)
            record.manifest = manifest
            record.package_path = package_path

    def mark_failed(self, job_id: str, error: str) -> None:
        with self._lock:
            record = self._require(job_id)
            record.status = JobStatus.failed
            record.error = error
            record.updated_at = datetime.now(timezone.utc)

    def package_path(self, job_id: str) -> Optional[Path]:
        with self._lock:
            record = self._require(job_id)
        return record.package_path
