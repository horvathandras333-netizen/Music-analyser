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
        CadenceRow(label="per beat", interval_s=0.414, gestures_in_clip=24.0, recommended=False, divides_evenly=True),
        CadenceRow(label="per bar", interval_s=1.655, gestures_in_clip=6.0, recommended=True, divides_evenly=True),
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
        tempo_drift_ms=0.0,
        loop_mode="ping_pong",
        cadence=cadence,
    )

    report = render_report(analysis, spec)

    assert "TRACK: Sunfire.wav" in report
    assert "BPM: 145.02" in report
    assert "First downbeat: 0.284s" in report
    assert "Duration: 9.931s (24 beats / 6.0 bars)" in report
    assert "[tempo drift: +0.0ms]" in report
    assert "Frames @24fps: 238 (residual drift +14ms, sub-frame)" in report
    assert "Loop mode: ping-pong (effective 19.862s)" in report
    assert "CADENCE" in report
    assert "per bar     1.655s   x6.0    <- recommended" in report
    assert "PROMPT FRAGMENT" in report
    assert "accent at 0.41s and 1.24s" in report
    assert "ADVISORY" in report


def test_bar_labeling_first_downbeat_is_bar_1():
    # First downbeat is at 0.284s. Starting selection at 0.284s must be Bar 1.
    analysis = TrackAnalysis(
        path=Path("Sunfire.wav"),
        sample_rate=44100,
        duration_s=60.0,
        bpm=145.0,
        bpm_confidence=0.95,
        bpm_alternates=[],
        beat_times=[0.284],
        downbeat_times=[0.284],
        meter=4,
    )
    spec = ClipSpec(
        start_s=0.284,
        end_s=10.215,
        beats=24,
        bars=6.0,
        duration_s=9.931,
        fps=24,
        frames=238,
        drift_ms=0.0,
        drift_is_subframe=True,
        tempo_drift_ms=0.0,
        loop_mode="ping_pong",
        cadence=[],
    )
    report = render_report(analysis, spec)
    assert "(bars 1-7)" in report


def test_report_renders_tempo_drift():
    analysis = TrackAnalysis(
        path=Path("Test.wav"),
        sample_rate=44100,
        duration_s=60.0,
        bpm=120.0,
        bpm_confidence=0.9,
        bpm_alternates=[],
        beat_times=[0.0],
        downbeat_times=[0.0],
        meter=4,
    )
    spec = ClipSpec(
        start_s=0.0,
        end_s=10.05,
        beats=20,
        bars=5.0,
        duration_s=10.05,
        fps=24,
        frames=241,
        drift_ms=0.0,
        drift_is_subframe=True,
        tempo_drift_ms=50.0,
        loop_mode="ping_pong",
        cadence=[],
    )
    report = render_report(analysis, spec)
    assert "[tempo drift: +50.0ms]" in report


def test_report_shows_loop_incompatible_cadence():
    analysis = TrackAnalysis(
        path=Path("Test.wav"),
        sample_rate=44100,
        duration_s=60.0,
        bpm=120.0,
        bpm_confidence=0.9,
        bpm_alternates=[],
        beat_times=[0.0],
        downbeat_times=[0.0],
        meter=4,
    )
    cadence = [
        CadenceRow(label="per 2 bars", interval_s=4.0, gestures_in_clip=2.5, recommended=False, divides_evenly=False),
    ]
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
        cadence=cadence,
    )
    report = render_report(analysis, spec)
    assert "(loop-incompatible)" in report


def test_prompt_fragment_includes_accent_line():
    analysis = TrackAnalysis(
        path=Path("Test.wav"),
        sample_rate=44100,
        duration_s=60.0,
        bpm=145.0,
        bpm_confidence=0.9,
        bpm_alternates=[],
        beat_times=[0.0],
        downbeat_times=[0.0],
        meter=4,
    )
    spec = ClipSpec(
        start_s=0.0,
        end_s=9.931,
        beats=24,
        bars=6.0,
        duration_s=9.931,
        fps=24,
        frames=238,
        drift_ms=0.0,
        drift_is_subframe=True,
        tempo_drift_ms=0.0,
        loop_mode="ping_pong",
        cadence=[],
    )
    report = render_report(analysis, spec)
    assert "sharp shoulder accent at 0.41s and 1.24s" in report


def test_report_includes_bpm_alternates_when_low_confidence():
    analysis = TrackAnalysis(
        path=Path("LowConf.wav"),
        sample_rate=44100,
        duration_s=60.0,
        bpm=145.0,
        bpm_confidence=0.65,
        bpm_alternates=[72.5, 290.0],
        beat_times=[0.0],
        downbeat_times=[0.0],
        meter=4,
    )
    spec = ClipSpec(
        start_s=0.0,
        end_s=10.0,
        beats=24,
        bars=6.0,
        duration_s=10.0,
        fps=24,
        frames=240,
        drift_ms=0.0,
        drift_is_subframe=True,
        tempo_drift_ms=0.0,
        loop_mode="ping_pong",
        cadence=[],
    )
    report = render_report(analysis, spec)
    assert "alternates: 72.50, 290.00" in report


def test_report_shows_top_3_candidates():
    analysis = TrackAnalysis(
        path=Path("Test.wav"),
        sample_rate=44100,
        duration_s=60.0,
        bpm=145.0,
        bpm_confidence=0.9,
        bpm_alternates=[],
        beat_times=[0.0],
        downbeat_times=[0.0],
        meter=4,
    )
    spec = ClipSpec(
        start_s=0.0,
        end_s=9.931,
        beats=24,
        bars=6.0,
        duration_s=9.931,
        fps=24,
        frames=238,
        drift_ms=0.0,
        drift_is_subframe=True,
        tempo_drift_ms=0.0,
        loop_mode="ping_pong",
        cadence=[],
    )
    candidates = [(24, 6.0, 9.931), (16, 4.0, 6.621), (32, 8.0, 13.241)]
    report = render_report(analysis, spec, candidates=candidates)
    assert "TOP CANDIDATES" in report
    assert "#1: 24 beats (6.0 bars, 9.931s) [selected]" in report
    assert "#2: 16 beats (4.0 bars, 6.621s)" in report
    assert "#3: 32 beats (8.0 bars, 13.241s)" in report


def test_cli_analyze_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    wav_path = tmp_path / "test_track.wav"
    generate_click_wav(wav_path, bpm=120.0, duration_s=12.0)

    exit_code = cli.main(["analyze", str(wav_path), "--target", "10", "--fps", "24"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "TRACK: test_track.wav" in captured.out
    assert "CLIP SPEC" in captured.out
    assert "Frames @24fps:" in captured.out
    assert "TOP CANDIDATES" in captured.out
    assert "PROMPT FRAGMENT" in captured.out
