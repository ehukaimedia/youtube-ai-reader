from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

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
    frame_limit: int = Field(40, ge=1, le=500)


class FrameMetadata(BaseModel):
    filename: str
    timestamp_sec: float
    width: int
    height: int
    scene_change: bool = False
    scene_score: float = 0.0
    ocr_text: Optional[str] = None
    caption: Optional[str] = None


class TranscriptSource(str, Enum):
    youtube = "youtube"
    whisper = "whisper"


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str
    source: TranscriptSource
    confidence: Optional[float] = None


class TranscriptBundle(BaseModel):
    best_source: TranscriptSource
    sources: List[TranscriptSource]
    segments: List[TranscriptSegment]
    alternates: Dict[TranscriptSource, List[TranscriptSegment]] = Field(default_factory=dict)


class Manifest(BaseModel):
    video_url: HttpUrl
    language: str
    interval_sec: int
    frame_limit: int
    frame_scene_threshold: float
    frames: List[FrameMetadata]
    frames_json_path: str
    transcript_items: int
    transcript_json_path: str
    transcript_bundle_path: str
    transcript_sources: List[TranscriptSource]
    transcript_primary_source: TranscriptSource
    markdown_path: str
    quality_report_path: str
    generated_at: datetime
    ocr_enabled: bool
    caption_model: Optional[str] = None


class JobResponse(BaseModel):
    id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None
    manifest: Optional[Manifest] = None
