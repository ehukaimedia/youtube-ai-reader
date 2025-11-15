from __future__ import annotations

import math
from pathlib import Path
from typing import List

import cv2
import numpy as np

from .captions import extract_ocr_text, generate_caption
from .config import settings
from .schemas import FrameMetadata


def extract_frames(
    video_path: Path,
    job_directory: Path,
    interval: int,
    min_width: int,
    max_width: int,
    frame_limit: int,
    scene_threshold: float = 0.28,
) -> List[FrameMetadata]:
    """Capture interval-based frames augmented with simple scene detection."""

    frames_dir = job_directory / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(str(video_path))
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    frame_interval = max(int(fps * interval), 1)

    metadata: List[FrameMetadata] = []
    prev_gray = None
    frame_index = 0
    next_interval_target = 0

    while frame_index < total_frames or total_frames == 0:
        ret, frame = capture.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        scene_score = 0.0
        is_scene_change = False
        if prev_gray is not None:
            diff = cv2.absdiff(gray, prev_gray)
            scene_score = float(np.mean(diff) / 255.0)
            is_scene_change = scene_score >= scene_threshold

        should_capture = frame_index >= next_interval_target or is_scene_change
        if should_capture and len(metadata) < frame_limit:
            timestamp_sec = frame_index / fps if fps else 0.0
            frame_path = frames_dir / f"frame_{len(metadata) + 1:04d}.png"
            resized = _resize_frame(frame, min_width, max_width)
            cv2.imwrite(str(frame_path), resized)

            height, width = resized.shape[:2]
            ocr_text = extract_ocr_text(frame_path) if settings.enable_ocr else None
            caption = generate_caption(frame_path)

            metadata.append(
                FrameMetadata(
                    filename=f"frames/{frame_path.name}",
                    timestamp_sec=round(timestamp_sec, 2),
                    width=int(width),
                    height=int(height),
                    scene_change=is_scene_change,
                    scene_score=round(scene_score, 4),
                    ocr_text=ocr_text,
                    caption=caption,
                )
            )
            next_interval_target = frame_index + frame_interval

        prev_gray = gray
        frame_index += 1

        if len(metadata) >= frame_limit:
            break

    capture.release()
    return metadata


def _resize_frame(frame: np.ndarray, min_width: int, max_width: int) -> np.ndarray:
    height, width = frame.shape[:2]
    target_width = int(min(max(width, min_width), max_width))
    if target_width == width:
        return frame

    scale = target_width / float(width)
    target_height = int(math.floor(height * scale))
    return cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)
