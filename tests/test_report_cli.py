from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

import cli
from models import CadenceRow, ClipSpec, TrackAnalysis
from report.render import render_report
from spec.cadence import build_cadence_ladder


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


def _make_analysis(**overrides):
    defaults = {
        "path": Path("Test.wav"),
        "sample_rate": 44100,
        "duration_s": 60.0,
        "bpm": 145.0,
        "bpm_confidence": 0.9,
        "bpm_alternates": [],
        "beat_times": [0.0],
        "downbeat_times": [0.0],
        "meter": 4,
    }
    defaults.update(overrides)
    return TrackAnalysis(**defaults)


def _make_spec(**overrides):
    defaults = {
        "start_s": 0.0,
        "end_s": 9.931,
        "beats": 24,
        "bars": 6.0,
        "duration_s": 9.931,
        "fps": 24,
        "frames": 238,
        "drift_ms": -14.33,
        "drift_is_subframe": True,
        "tempo_drift_ms": 0.0,
        "loop_mode": "true_cycle",
        "cadence": [],
    }
    defaults.update(overrides)
    return ClipSpec(**defaults)


def test_render_report():
    analysis = _make_analysis(
        path=Path("Sunfire.wav"), bpm=145.02, bpm_confidence=0.91,
        bpm_alternates=[72.51, 290.04],
        beat_times=[0.284, 0.698], downbeat_times=[0.284, 1.939],
    )
    cadence = [
        CadenceRow(label="per beat", interval_s=0.414, gestures_in_clip=24.0, recommended=False, divides_evenly=True),
        CadenceRow(label="per bar", interval_s=1.655, gestures_in_clip=6.0, recommended=True, divides_evenly=True),
    ]
    spec = _make_spec(
        start_s=32.114, end_s=42.045, drift_ms=14.0,
        loop_mode="true_cycle", cadence=cadence,
    )

    report = render_report(analysis, spec)

    assert "TRACK: Sunfire.wav" in report
    assert "BPM: 145.02" in report
    assert "First downbeat: 0.284s" in report
    assert "Duration: 9.931s (24 beats / 6 bars)" in report
    assert "[tempo drift: +0.0ms]" in report
    assert "Frames @24fps: 238" in report
    assert "CADENCE" in report
    assert "per bar     1.655s   x6.0    <- recommended" in report
    assert "PROMPT FRAGMENT" in report
    assert "accent at 0.41s and 1.24s" in report
    assert "ADVISORY" in report


def test_bar_labeling_first_downbeat_is_bar_1():
    analysis = _make_analysis(
        path=Path("Sunfire.wav"), bpm=145.0, bpm_confidence=0.95,
        beat_times=[0.284], downbeat_times=[0.284],
    )
    spec = _make_spec(start_s=0.284, end_s=10.215, bars=6.0)
    report = render_report(analysis, spec)
    # 6-bar region starting at bar 1 -> bars 1-6 (inclusive)
    assert "(bars 1-6)" in report


@pytest.mark.parametrize("bars,expected_label", [
    (1, "bars 1-1"),
    (4, "bars 1-4"),
    (7, "bars 1-7"),
    (8, "bars 1-8"),
])
def test_bar_range_label_length(bars, expected_label):
    analysis = _make_analysis(downbeat_times=[0.0])
    spec = _make_spec(start_s=0.0, bars=float(bars))
    report = render_report(analysis, spec)
    assert f"({expected_label})" in report


def test_report_renders_tempo_drift():
    analysis = _make_analysis(bpm=120.0)
    spec = _make_spec(
        end_s=10.05, beats=20, bars=5.0, duration_s=10.05,
        frames=241, drift_ms=0.0, tempo_drift_ms=50.0,
    )
    report = render_report(analysis, spec)
    assert "[tempo drift: +50.0ms]" in report


def test_report_shows_loop_incompatible_cadence():
    analysis = _make_analysis(bpm=120.0)
    cadence = [
        CadenceRow(label="per 2 bars", interval_s=4.0, gestures_in_clip=2.5, recommended=False, divides_evenly=False),
    ]
    spec = _make_spec(
        beats=20, bars=5.0, duration_s=10.0, frames=240,
        drift_ms=0.0, loop_mode="ping_pong", cadence=cadence,
    )
    report = render_report(analysis, spec)
    assert "(loop-incompatible)" in report


def test_true_cycle_prompt_language():
    analysis = _make_analysis()
    spec = _make_spec(loop_mode="true_cycle")
    report = render_report(analysis, spec)
    # true_cycle prompt says pose at end matches pose at 0
    assert "identical to pose at" in report
    assert "0.00s" in report
    # Should NOT contain the ping-pong reversed motion warning
    assert "reverses motion" not in report


def test_ping_pong_prompt_language():
    analysis = _make_analysis()
    spec = _make_spec(loop_mode="ping_pong")
    report = render_report(analysis, spec)
    # ping_pong prompt says do not return to opening pose
    assert "do not return to the opening pose" in report
    # Should contain the reversed motion warning in advisory
    assert "reverses motion" in report


def test_prompt_fragment_includes_accent_line():
    analysis = _make_analysis()
    spec = _make_spec()
    report = render_report(analysis, spec)
    assert "sharp shoulder accent at 0.41s and 1.24s" in report


def test_report_includes_bpm_alternates_when_low_confidence():
    analysis = _make_analysis(
        path=Path("LowConf.wav"), bpm_confidence=0.65,
        bpm_alternates=[72.5, 290.0],
    )
    spec = _make_spec(
        beats=24, bars=6.0, duration_s=10.0, frames=240, drift_ms=0.0,
    )
    report = render_report(analysis, spec)
    assert "alternates: 72.50, 290.00" in report


def test_report_shows_top_3_candidates():
    analysis = _make_analysis()
    spec = _make_spec()
    candidates = [(24, 6.0, 9.931), (16, 4.0, 6.621), (32, 8.0, 13.241)]
    report = render_report(analysis, spec, candidates=candidates)
    assert "TOP CANDIDATES" in report
    assert "#1: 24 beats" in report
    assert "[selected]" in report
    assert "#2: 16 beats" in report
    assert "#3: 32 beats" in report


def test_candidates_ranked_against_target():
    analysis = _make_analysis()
    spec = _make_spec(duration_s=5.0, beats=12, bars=3.0, frames=120)
    # Pass target 10s — candidates should be ranked against 10s, not 5s
    report = render_report(analysis, spec, target_duration_s=10.0)
    assert "Target: 10.0s" in report


def test_candidate_shows_effective_duration():
    analysis = _make_analysis()
    spec = _make_spec(loop_mode="ping_pong")
    candidates = [(24, 6.0, 9.931)]
    report = render_report(analysis, spec, candidates=candidates)
    assert "eff " in report


def test_bar_count_never_rounded():
    analysis = _make_analysis()
    # A spec with 3.75 bars should print "3.75", not "3.8"
    spec = _make_spec(beats=15, bars=3.75)
    report = render_report(analysis, spec)
    assert "3.75 bars" in report


def test_prompt_uses_frame_aligned_duration():
    analysis = _make_analysis()
    # 238 frames at 24fps = 9.916667s, ideal 9.931s
    # Frame-aligned rounds to 9.92, not 9.93
    spec = _make_spec(frames=238, duration_s=9.931, loop_mode="true_cycle")
    report = render_report(analysis, spec)
    # The prompt should use frame-aligned duration (238/24 = 9.916..)
    frame_aligned = 238 / 24
    assert f"{frame_aligned:.2f}s is identical to pose at" in report


def test_7_bar_selection_2bar_row_loop_incompatible():
    # 28 beats / 7 bars at 120 BPM
    cadence = build_cadence_ladder(120.0, beats=28, meter=4)
    per_2bars = next(row for row in cadence if row.label == "per 2 bars")
    assert per_2bars.gestures_in_clip == 3.5
    assert per_2bars.divides_evenly is False

    analysis = _make_analysis(bpm=120.0)
    spec = _make_spec(
        beats=28, bars=7.0, duration_s=14.0, frames=336, drift_ms=0.0,
        cadence=cadence,
    )
    report = render_report(analysis, spec)
    assert "x3.5" in report
    assert "(loop-incompatible)" in report


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
    assert "Target: 10.0s" in captured.out


def test_cli_dump_grid_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    wav_path = tmp_path / "test_dump.wav"
    generate_click_wav(wav_path, bpm=120.0, duration_s=8.0)

    exit_code = cli.main(["dump-grid", str(wav_path)])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "DOWNBEAT TIMES" in captured.out
    assert "CONSECUTIVE INTERVALS" in captured.out
