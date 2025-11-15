from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import ffmpeg
from PIL import Image
from youtube_transcript_api import YouTubeTranscriptApi

from . import storage
from .jobs import JobStore
from .schemas import FrameMetadata, JobCreateRequest, Manifest

YTDLP_CMD = [
    "yt-dlp",
    "-f",
    "best[ext=mp4]",
    "--quiet",
    "--no-warnings",
    "-o",
]


def run_pipeline(job_id: str, config: JobCreateRequest, store: JobStore) -> None:
    job_directory = storage.job_dir(job_id)
    store.mark_in_progress(job_id)
    video_url = str(config.video_url)
    try:
        video_path = download_video(video_url, job_directory)
        transcript = fetch_transcript(video_url, config.language)
        storage.write_json(job_directory / "transcript.json", transcript)
        frames = capture_frames(
            video_path=video_path,
            job_directory=job_directory,
            interval=config.interval_sec,
            min_width=config.min_width,
            max_width=config.max_width,
            frame_limit=config.frame_limit,
        )
        storage.write_json(job_directory / "frames.json", [frame.model_dump() for frame in frames])
        markdown_path = write_markdown(job_directory, video_url, transcript, frames)
        manifest = Manifest(
            video_url=video_url,
            language=config.language,
            interval_sec=config.interval_sec,
            frames=frames,
            transcript_items=len(transcript),
            markdown_path=markdown_path.name,
            transcript_json_path="transcript.json",
            generated_at=datetime.now(timezone.utc),
        )
        storage.write_json(job_directory / "manifest.json", manifest.model_dump(mode="json"))
        package_path = storage.package_directory(job_directory)
        store.mark_complete(job_id, manifest, package_path)
    except Exception as exc:  # pragma: no cover - surfaced via API response
        store.mark_failed(job_id, str(exc))
        raise


def download_video(video_url: str, job_directory: Path) -> Path:
    template = str(job_directory / "%(id)s.%(ext)s")
    subprocess.check_call(YTDLP_CMD + [template, video_url])
    mp4s = sorted(job_directory.glob("*.mp4"))
    if not mp4s:
        raise RuntimeError("Video download failed")
    return mp4s[0]


def fetch_transcript(video_url: str, language: str) -> List[dict]:
    video_id = extract_video_id(video_url)
    lang_chain = [language]
    if language != "en":
        lang_chain.append("en")
    api = YouTubeTranscriptApi()
    return api.fetch(video_id, languages=lang_chain).to_raw_data()


def capture_frames(
    video_path: Path,
    job_directory: Path,
    interval: int,
    min_width: int,
    max_width: int,
    frame_limit: int,
) -> List[FrameMetadata]:
    frames_dir = job_directory / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    scale = f"if(gt(iw,{max_width}),{max_width},if(lt(iw,{min_width}),{min_width},iw))"
    (
        ffmpeg.input(str(video_path))
        .filter_("fps", fps=f"1/{interval}")
        .filter_("scale", scale, "-2")
        .output(str(frames_dir / "frame_%04d.png"), vframes=frame_limit, vsync="vfr")
        .overwrite_output()
        .run(quiet=True)
    )

    frames: List[FrameMetadata] = []
    for index, frame_path in enumerate(sorted(frames_dir.glob("frame_*.png"))):
        with Image.open(frame_path) as img:
            width, height = img.size
        frames.append(
            FrameMetadata(
                filename=f"frames/{frame_path.name}",
                timestamp_sec=round(interval * index, 2),
                width=width,
                height=height,
            )
        )
    return frames


def write_markdown(
    job_directory: Path,
    video_url: str,
    transcript: List[dict],
    frames: List[FrameMetadata],
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
        lines.append(f"- [{item['start']:.1f}s] {item['text']}")
    lines.append("")
    lines.append("## Frames")
    for idx, frame in enumerate(frames, start=1):
        lines.append(f"![Frame {idx}]({frame.filename}) — t={frame.timestamp_sec}s")
    lines.append("")
    path = job_directory / "transcript.md"
    storage.write_text(path, "\n".join(lines).strip() + "\n")
    return path


def extract_video_id(url: str) -> str:
    match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    if not match:
        raise ValueError("Unable to extract video ID")
    return match.group(1)
