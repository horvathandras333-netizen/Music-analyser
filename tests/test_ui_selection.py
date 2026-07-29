from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.waveform import WaveformWidget


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def generate_test_wav(path: Path, bpm: float = 120.0, duration_s: float = 10.0, sr: int = 44100):
    num_samples = int(sr * duration_s)
    audio = np.zeros(num_samples, dtype=np.float32)
    beat_samples = int(sr * (60.0 / bpm))
    click_dur = int(0.01 * sr)
    t = np.linspace(0, 0.01, click_dur, endpoint=False)
    click = (np.sin(2 * np.pi * 1000 * t) * np.exp(-t * 300)).astype(np.float32)

    for pos in range(0, num_samples - click_dur, beat_samples):
        audio[pos : pos + click_dur] += click

    sf.write(path, audio, sr, subtype="FLOAT")


def test_snap_time_to_grid_detected(qapp):
    widget = WaveformWidget()
    audio = np.zeros(44100 * 10, dtype=np.float32)
    beat_times = [0.0, 0.5, 1.0, 1.5, 2.0]
    downbeat_times = [0.0, 2.0]
    widget.set_track(audio, 44100, beat_times, downbeat_times, bpm=120.0)

    widget.grid_mode = "detected"
    assert widget.snap_time_to_grid(0.48) == 0.5
    assert widget.snap_time_to_grid(1.02) == 1.0


def test_snap_time_to_grid_arithmetic(qapp):
    widget = WaveformWidget()
    audio = np.zeros(44100 * 10, dtype=np.float32)
    beat_times = [0.2, 0.7, 1.2]
    downbeat_times = [0.2]
    widget.set_track(audio, 44100, beat_times, downbeat_times, bpm=120.0)

    widget.grid_mode = "arithmetic"
    # period = 0.5s starting at 0.2s -> expected beats at 0.2, 0.7, 1.2
    assert widget.snap_time_to_grid(0.72) == 0.7
    assert widget.snap_time_to_grid(1.18) == 1.2


def test_selection_changed_updates_spec_panel(tmp_path: Path, qapp):
    wav_path = tmp_path / "test_ui.wav"
    generate_test_wav(wav_path, bpm=120.0, duration_s=10.0)

    window = MainWindow()
    window.load_track(wav_path)

    assert window.waveform.selection_start_s is not None
    assert window.waveform.selection_end_s is not None

    display_text = window.spec_panel.text_display.toPlainText()
    assert "TRACK: test_ui.wav" in display_text
    assert "CLIP SPEC" in display_text
    assert "PROMPT FRAGMENT" in display_text
