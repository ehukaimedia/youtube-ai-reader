import pytest

from app import utils


def test_extract_video_id_success():
    assert utils.extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_invalid():
    with pytest.raises(ValueError):
        utils.extract_video_id("https://example.com")


def test_ensure_commands_available(monkeypatch):
    called = {}

    def fake_which(cmd):
        called[cmd] = True
        return "/usr/bin/" + cmd

    monkeypatch.setattr(utils.shutil, "which", fake_which)
    utils.ensure_commands_available(["ffmpeg", "yt-dlp"])
    assert set(called.keys()) == {"ffmpeg", "yt-dlp"}


def test_ensure_commands_missing(monkeypatch):
    monkeypatch.setattr(utils.shutil, "which", lambda _: None)
    with pytest.raises(RuntimeError):
        utils.ensure_commands_available(["missing-binary"])
