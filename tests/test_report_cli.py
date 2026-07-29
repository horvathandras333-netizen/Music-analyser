from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

import cli
from models import CadenceRow, ClipSpec, TrackAnalysis
from report.render import render_report


def generate_click_wav(path: Path, bpm: float = 145.0, duration_s: float = 12.0, sr: int = 44100):
    num_samples = int(sr * duration_s)
    audio = np.zeros(num_samples, dtype=np.float32)
    beat_samples = int(sr * (60.0 / bpm))
    click_dur = int(0.01 * sr)
    t = np.linspace(0, 0.01, click_dur, endpoint=False)
    click = (np.sin(2 * np.pi * 1000 * t) * np.exp(-t * 300)).astype(np.float32)

    for pos in range(0, num_samples - click_dur, beat_samples):
        audio[pos : pos + click_dur] += click

    sf.write(path, audio, sr, subtype="FLOAT")


def test_render_report():
    analysis = TrackAnalysis(
        path=Path("Sunfire.wav"),
        sample_rate=44100,
        duration_s=60.0,
        bpm=145.02,
        bpm_confidence=0.91,
        bpm_alternates=[72.51, 290.04],
        beat_times=[0.284, 0.698],
        downbeat_times=[0.284, 1.939],
        meter=4,
    )
    cadence = [
        CadenceRow(label="per beat", interval_s=0.414, gestures_in_clip=24.0, recommended=False),
        CadenceRow(label="per bar", interval_s=1.655, gestures_in_clip=6.0, recommended=True),
    ]
    spec = ClipSpec(
        start_s=32.114,
        end_s=42.045,
        beats=24,
        bars=6.0,
        duration_s=9.931,
        fps=24,
        frames=238,
        drift_ms=14.0,
        drift_is_subframe=True,
        loop_mode="ping_pong",
        cadence=cadence,
    )

    report = render_report(analysis, spec)

    assert "TRACK: Sunfire.wav" in report
    assert "BPM: 145.02" in report
    assert "First downbeat: 0.284s" in report
    assert "Duration: 9.931s (24 beats / 6.0 bars)" in report
    assert "Frames @24fps: 238 (residual drift +14ms, sub-frame)" in report
    assert "Loop mode: ping-pong (effective 19.862s)" in report
    assert "CADENCE" in report
    assert "per bar     1.655s   x6.0    <- recommended" in report
    assert "PROMPT FRAGMENT" in report
    assert "ADVISORY" in report


def test_cli_analyze_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    wav_path = tmp_path / "test_track.wav"
    generate_click_wav(wav_path, bpm=120.0, duration_s=12.0)

    exit_code = cli.main(["analyze", str(wav_path), "--target", "10", "--fps", "24"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "TRACK: test_track.wav" in captured.out
    assert "CLIP SPEC" in captured.out
    assert "Frames @24fps:" in captured.out
    assert "PROMPT FRAGMENT" in captured.out
