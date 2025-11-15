from __future__ import annotations

import logging
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from . import storage
from .config import settings
from .jobs import JobStore
from .quality import build_quality_report
from .schemas import FrameMetadata, JobCreateRequest, Manifest, TranscriptSegment
from .transcripts import build_transcript_bundle
from .utils import ensure_commands_available
from .vision import extract_frames

YTDLP_CMD = [
    "yt-dlp",
    "-f",
    "best[ext=mp4]",
    "--quiet",
    "--no-warnings",
    "-o",
]


logger = logging.getLogger(__name__)

SCENE_THRESHOLD = settings.frame_scene_threshold


def run_pipeline(job_id: str, config: JobCreateRequest, store: JobStore) -> None:
    job_directory = storage.job_dir(job_id)
    store.mark_in_progress(job_id)
    video_url = str(config.video_url)
    ensure_commands_available(["yt-dlp", "ffmpeg"])
    logger.info("job %s started with interval=%s frame_limit=%s", job_id, config.interval_sec, config.frame_limit)
    try:
        video_path = download_video(video_url, job_directory)
        transcript_bundle = build_transcript_bundle(video_url, video_path, config.language)
        transcript_segments = transcript_bundle.segments
        if not transcript_segments:
            raise RuntimeError("Transcript extraction returned no segments")
        storage.write_json(
            job_directory / "transcript_bundle.json",
            transcript_bundle.model_dump(mode="json"),
        )
        storage.write_json(
            job_directory / "transcript.json",
            [segment.model_dump(mode="json") for segment in transcript_segments],
        )

        frames = extract_frames(
            video_path=video_path,
            job_directory=job_directory,
            interval=config.interval_sec,
            min_width=config.min_width,
            max_width=config.max_width,
            frame_limit=config.frame_limit,
            scene_threshold=SCENE_THRESHOLD,
        )
        if not frames:
            raise RuntimeError("No frames captured from video stream")
        storage.write_json(job_directory / "frames.json", [frame.model_dump(mode="json") for frame in frames])

        quality = build_quality_report(transcript_segments, frames)
        storage.write_json(job_directory / "quality_report.json", quality.as_dict())

        markdown_path = write_markdown(job_directory, video_url, transcript_segments, frames)
        manifest = Manifest(
            video_url=video_url,
            language=config.language,
            interval_sec=config.interval_sec,
            frame_limit=config.frame_limit,
            frame_scene_threshold=SCENE_THRESHOLD,
            frames=frames,
            frames_json_path="frames.json",
            transcript_items=len(transcript_segments),
            transcript_json_path="transcript.json",
            transcript_bundle_path="transcript_bundle.json",
            transcript_sources=transcript_bundle.sources,
            transcript_primary_source=transcript_bundle.best_source,
            markdown_path=markdown_path.name,
            quality_report_path="quality_report.json",
            generated_at=datetime.now(timezone.utc),
            ocr_enabled=ocr_available(),
            caption_model=settings.ollama_model,
        )
        storage.write_json(job_directory / "manifest.json", manifest.model_dump(mode="json"))
        package_path = storage.package_directory(job_directory)
        store.mark_complete(job_id, manifest, package_path)
        logger.info(
            "job %s complete | transcript_segments=%s frames=%s warnings=%s",
            job_id,
            len(transcript_segments),
            len(frames),
            quality.warnings,
        )
    except Exception as exc:  # pragma: no cover - surfaced via API response
        logger.exception("job %s failed", job_id)
        store.mark_failed(job_id, str(exc))
        raise


def download_video(video_url: str, job_directory: Path) -> Path:
    template = str(job_directory / "%(id)s.%(ext)s")
    attempts = settings.download_retries
    for attempt in range(1, attempts + 1):
        try:
            subprocess.run(
                YTDLP_CMD + [template, video_url],
                check=True,
                timeout=settings.download_timeout_sec,
            )
            break
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            if attempt >= attempts:
                raise RuntimeError("Video download failed") from exc
            backoff = settings.download_retry_backoff_sec * attempt
            logger.warning("Download failed (attempt %s/%s). Retrying in %.1fs", attempt, attempts, backoff)
            time.sleep(backoff)
    mp4s = sorted(job_directory.glob("*.mp4"))
    if not mp4s:
        raise RuntimeError("Video download failed")
    return mp4s[0]


def write_markdown(
    job_directory: Path,
    video_url: str,
    transcript: list[TranscriptSegment],
    frames: list[FrameMetadata],
) -> Path:
    lines = [
        f"# AI Bundle for {video_url}",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- Transcript entries: {len(transcript)}",
        f"- Frames captured: {len(frames)}",
        "",
        "## Transcript",
    ]
    for item in transcript:
        lines.append(f"- [{item.start:.1f}s] {item.text}")
    lines.append("")
    lines.append("## Frames")
    for idx, frame in enumerate(frames, start=1):
        lines.append(f"![Frame {idx}]({frame.filename}) — t={frame.timestamp_sec}s")
    lines.append("")
    path = job_directory / "transcript.md"
    storage.write_text(path, "\n".join(lines).strip() + "\n")
    return path


def ocr_available() -> bool:
    if not settings.enable_ocr:
        return False
    try:
        import pytesseract  # type: ignore  # pragma: no cover

        _ = pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False
