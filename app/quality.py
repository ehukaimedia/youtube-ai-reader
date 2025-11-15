from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .schemas import FrameMetadata, TranscriptSegment


@dataclass
class QualityReport:
    frame_count: int
    transcript_count: int
    transcript_duration_sec: float
    last_frame_timestamp: float
    coverage_ratio: float
    warnings: List[str]

    def as_dict(self) -> dict:
        return {
            "frame_count": self.frame_count,
            "transcript_count": self.transcript_count,
            "transcript_duration_sec": self.transcript_duration_sec,
            "last_frame_timestamp": self.last_frame_timestamp,
            "coverage_ratio": round(self.coverage_ratio, 3),
            "warnings": self.warnings,
        }


def build_quality_report(segments: List[TranscriptSegment], frames: List[FrameMetadata]) -> QualityReport:
    transcript_duration = segments[-1].end if segments else 0.0
    last_frame_ts = frames[-1].timestamp_sec if frames else 0.0
    coverage = (last_frame_ts / transcript_duration) if transcript_duration else 0.0
    warnings: List[str] = []

    if not frames:
        warnings.append("no_frames")
    if not segments:
        warnings.append("no_transcript")
    if frames and segments and coverage < 0.5:
        warnings.append("low_frame_coverage")

    return QualityReport(
        frame_count=len(frames),
        transcript_count=len(segments),
        transcript_duration_sec=round(transcript_duration, 2),
        last_frame_timestamp=round(last_frame_ts, 2),
        coverage_ratio=coverage,
        warnings=warnings,
    )
