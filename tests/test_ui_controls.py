from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from models import CadenceRow, ClipSpec, TrackAnalysis
from ui.main_window import MainWindow
from ui.spec_panel import SpecPanel


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def generate_test_wav(path: Path, bpm: float = 120.0, duration_s: float = 8.0, sr: int = 44100):
    num_samples = int(sr * duration_s)
    audio = np.zeros(num_samples, dtype=np.float32)
    beat_samples = int(sr * (60.0 / bpm))
    click_dur = int(0.01 * sr)
    t = np.linspace(0, 0.01, click_dur, endpoint=False)
    click = (np.sin(2 * np.pi * 1000 * t) * np.exp(-t * 300)).astype(np.float32)

    for pos in range(0, num_samples - click_dur, beat_samples):
        audio[pos : pos + click_dur] += click

    sf.write(path, audio, sr, subtype="FLOAT")


def test_copy_button_clipboard(qapp):
    panel = SpecPanel()
    analysis = TrackAnalysis(
        path=Path("test.wav"),
        sample_rate=44100,
        duration_s=10.0,
        bpm=120.0,
        bpm_confidence=0.9,
        bpm_alternates=[60.0, 240.0],
        beat_times=[0.0, 0.5],
        downbeat_times=[0.0],
        meter=4,
    )
    spec = ClipSpec(
        start_s=0.0,
        end_s=10.0,
        beats=20,
        bars=5.0,
        duration_s=10.0,
        fps=24,
        frames=240,
        drift_ms=0.0,
        drift_is_subframe=True,
        tempo_drift_ms=0.0,
        loop_mode="ping_pong",
        cadence=[CadenceRow(label="per bar", interval_s=2.0, gestures_in_clip=5.0, recommended=True, divides_evenly=True)],
    )
    panel.update_spec(analysis, spec)

    panel.copy_to_clipboard()

    clipboard_text = QGuiApplication.clipboard().text()
    assert "TRACK: test.wav" in clipboard_text
    assert "CLIP SPEC" in clipboard_text


def test_controls_update_spec(tmp_path: Path, qapp):
    wav_path = tmp_path / "test_controls.wav"
    generate_test_wav(wav_path, bpm=120.0, duration_s=8.0)

    window = MainWindow()
    window.load_track(wav_path)

    orig_bpm = window.current_analysis.bpm

    # Test FPS change
    window.combo_fps.setCurrentText("30")
    assert window.current_fps == 30
    assert "Frames @30fps:" in window.spec_panel.text_display.toPlainText()

    # Test BPM Halve
    window.btn_bpm_halve.click()
    assert window.current_analysis.bpm == pytest.approx(orig_bpm / 2.0, abs=0.05)

    # Test BPM Double
    window.btn_bpm_double.click()
    assert window.current_analysis.bpm == pytest.approx(orig_bpm, abs=0.05)

    # Test Loop Mode change
    window.combo_loop_mode.setCurrentText("true_cycle")
    assert window.current_loop_mode == "true_cycle"
    assert "Loop mode: true-cycle" in window.spec_panel.text_display.toPlainText()


def test_recent_files_menu(tmp_path: Path, qapp):
    wav_path = tmp_path / "test_recent.wav"
    generate_test_wav(wav_path, bpm=120.0, duration_s=5.0)

    window = MainWindow()
    window.settings.clear()
    window.load_track(wav_path)

    recent_actions = window.recent_menu.actions()
    assert len(recent_actions) == 1
    assert recent_actions[0].text() == "test_recent.wav"
