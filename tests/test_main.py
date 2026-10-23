import os
import time
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

from recorder.engine import ScreenRecorder, RecorderState
from recorder.storage import (
    get_default_recordings_dir,
    generate_recording_filename,
    list_recordings,
)


def test_storage_filename_generation():
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = generate_recording_filename(tmpdir, "mp4")
        assert filepath.startswith(tmpdir)
        assert filepath.endswith(".mp4")
        assert "Recording_" in filepath


def test_storage_list_recordings():
    with tempfile.TemporaryDirectory() as tmpdir:
        f1 = os.path.join(tmpdir, "Recording_2025-01-01.mp4")
        f2 = os.path.join(tmpdir, "ignore_me.txt")
        with open(f1, "wb") as f:
            f.write(b"dummy data")
        with open(f2, "wb") as f:
            f.write(b"ignore")

        recs = list_recordings(tmpdir)
        assert len(recs) == 1
        assert recs[0]["name"] == "Recording_2025-01-01.mp4"
        assert recs[0]["size_mb"] >= 0


def test_default_recordings_dir_creation():
    d = get_default_recordings_dir()
    assert os.path.isdir(d)


@patch("recorder.engine.cv2.VideoWriter")
@patch("recorder.engine.mss.mss")
def test_recorder_lifecycle(mock_mss_cls, mock_videowriter_cls):
    mock_sct = MagicMock()
    mock_sct.monitors = [
        {"width": 1920, "height": 1080, "top": 0, "left": 0},
        {"width": 1920, "height": 1080, "top": 0, "left": 0},
    ]
    # Fake 4-channel BGRA frame
    fake_bgra = np.zeros((1080, 1920, 4), dtype=np.uint8)
    mock_sct.grab.return_value = fake_bgra
    mock_mss_cls.return_value.__enter__.return_value = mock_sct

    mock_writer = MagicMock()
    mock_videowriter_cls.return_value = mock_writer

    with tempfile.TemporaryDirectory() as tmpdir:
        target_file = os.path.join(tmpdir, "test.mp4")
        recorder = ScreenRecorder(target_file, monitor_idx=1, fps=30)

        assert recorder.get_state() == RecorderState.IDLE
        started = recorder.start()
        assert started is True

        # Allow thread to capture at least one frame
        time.sleep(0.15)
        stats = recorder.get_stats()
        assert stats["state"] in (RecorderState.RECORDING, RecorderState.IDLE)

        recorder.pause()
        assert recorder.get_state() == RecorderState.PAUSED

        recorder.resume()
        assert recorder.get_state() == RecorderState.RECORDING

        stopped = recorder.stop()
        assert stopped is True
        assert recorder.get_state() == RecorderState.STOPPED
        assert mock_writer.release.called
