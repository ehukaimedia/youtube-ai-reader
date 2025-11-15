from app.quality import build_quality_report
from app.schemas import FrameMetadata, TranscriptSegment, TranscriptSource


def test_quality_report_flags_low_coverage():
    segments = [
        TranscriptSegment(start=0.0, end=10.0, text="hello", source=TranscriptSource.youtube),
        TranscriptSegment(start=10.0, end=20.0, text="world", source=TranscriptSource.youtube),
    ]
    frames = [
        FrameMetadata(filename="frames/frame_0001.png", timestamp_sec=1.0, width=100, height=100),
    ]

    report = build_quality_report(segments, frames)

    assert report.frame_count == 1
    assert report.transcript_count == 2
    assert "low_frame_coverage" in report.warnings
