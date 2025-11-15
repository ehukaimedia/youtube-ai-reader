from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class JobStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    complete = "complete"
    failed = "failed"


class JobCreateRequest(BaseModel):
    video_url: HttpUrl
    interval_sec: int = Field(30, ge=1, le=3600)
    min_width: int = Field(480, ge=1, le=7680)
    max_width: int = Field(1280, ge=1, le=7680)
    language: str = Field("en", min_length=2, max_length=5)
    frame_limit: int = Field(100, ge=1, le=500)


class FrameMetadata(BaseModel):
    filename: str
    timestamp_sec: float
    width: int
    height: int


class Manifest(BaseModel):
    video_url: HttpUrl
    language: str
    interval_sec: int
    frames: List[FrameMetadata]
    transcript_items: int
    markdown_path: str
    transcript_json_path: str
    generated_at: datetime


class JobResponse(BaseModel):
    id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None
    manifest: Optional[Manifest] = None
