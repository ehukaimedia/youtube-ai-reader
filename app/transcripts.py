from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from youtube_transcript_api import YouTubeTranscriptApi

from .config import settings
from .schemas import TranscriptBundle, TranscriptSegment, TranscriptSource
from .utils import extract_video_id

try:  # pragma: no cover - optional dependency
    from faster_whisper import WhisperModel
except Exception:  # pragma: no cover - best-effort import
    WhisperModel = None  # type: ignore


def build_transcript_bundle(video_url: str, video_path: Path, language: str) -> TranscriptBundle:
    """Fetches YouTube transcripts and, when available, aligns Whisper output."""

    youtube_segments = _fetch_youtube_segments(video_url, language)
    whisper_segments = _run_whisper(video_path, language)

    sources = []
    alternates = {}
    best_segments: List[TranscriptSegment] = []
    best_source = TranscriptSource.youtube

    if youtube_segments:
        sources.append(TranscriptSource.youtube)
        alternates[TranscriptSource.youtube] = youtube_segments
        best_segments = youtube_segments

    if whisper_segments:
        sources.append(TranscriptSource.whisper)
        alternates[TranscriptSource.whisper] = whisper_segments
        best_segments = whisper_segments
        best_source = TranscriptSource.whisper

    return TranscriptBundle(
        best_source=best_source,
        sources=sources,
        segments=best_segments,
        alternates=alternates,
    )


def _fetch_youtube_segments(video_url: str, language: str) -> List[TranscriptSegment]:
    transcript_api = YouTubeTranscriptApi()
    video_id = extract_video_id(video_url)
    languages = [language]
    if language != "en":
        languages.append("en")
    try:
        entries = transcript_api.fetch(video_id, languages=languages).to_raw_data()
    except Exception:
        return []

    segments: List[TranscriptSegment] = []
    for entry in entries:
        start = float(entry.get("start", 0.0))
        duration = float(entry.get("duration", 0.0))
        segments.append(
            TranscriptSegment(
                start=start,
                end=start + duration,
                text=entry.get("text", "").strip(),
                source=TranscriptSource.youtube,
            )
        )
    return segments


def _run_whisper(video_path: Path, language: str) -> List[TranscriptSegment]:
    if WhisperModel is None:
        return []

    try:
        model = WhisperModel(
            settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )
    except Exception:
        return []

    try:
        segments_iter, _ = model.transcribe(
            str(video_path),
            language=None if language == "auto" else language,
            beam_size=5,
        )
    except Exception:
        return []

    segments: List[TranscriptSegment] = []
    for item in segments_iter:
        segments.append(
            TranscriptSegment(
                start=float(item.start or 0.0),
                end=float(item.end or 0.0),
                text=(item.text or "").strip(),
                source=TranscriptSource.whisper,
                confidence=float(item.avg_logprob or 0.0),
            )
        )
    return segments
