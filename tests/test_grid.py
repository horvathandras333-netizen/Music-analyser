from pathlib import Path

import numpy as np
import soundfile as sf

from analysis.grid import analyze_track, generate_beat_grid
from models import TrackAnalysis


def generate_offset_click_track(
    bpm: float, offset_s: float, sample_rate: int = 44100, duration_s: float = 6.0
) -> np.ndarray:
    """Generate synthetic click track with an initial time offset."""
    num_samples = int(sample_rate * duration_s)
    audio = np.zeros(num_samples, dtype=np.float32)
    beat_interval_samples = int(sample_rate * (60.0 / bpm))
    offset_samples = int(sample_rate * offset_s)

    click_duration = int(0.01 * sample_rate)
    t_click = np.linspace(0, 0.01, click_duration, endpoint=False)
    click = (np.sin(2 * np.pi * 1000 * t_click) * np.exp(-t_click * 300)).astype(np.float32)

    for pos in range(offset_samples, num_samples - click_duration, beat_interval_samples):
        audio[pos : pos + click_duration] += click

    return audio


def test_generate_beat_grid_phase_and_spacing():
    sr = 44100
    bpm = 120.0
    offset_s = 0.2
    duration_s = 6.0
    audio = generate_offset_click_track(bpm, offset_s, sample_rate=sr, duration_s=duration_s)

    beat_times, downbeat_times = generate_beat_grid(audio, sr, bpm, meter=4)

    assert len(beat_times) > 0
    assert len(downbeat_times) > 0
    assert abs(beat_times[0] - offset_s) < 0.05

    # Check beat spacing — onset-refined beats may deviate slightly from arithmetic
    spacings = np.diff(beat_times)
    expected_spacing = 60.0 / bpm
    np.testing.assert_allclose(spacings, expected_spacing, atol=0.03)

    # Downbeats should be a subset of beat_times spaced every 4 beats
    assert len(downbeat_times) <= (len(beat_times) // 4) + 1


def test_analyze_track_integration(tmp_path: Path):
    sr = 44100
    bpm = 145.0
    audio = generate_offset_click_track(bpm, offset_s=0.1, sample_rate=sr, duration_s=5.0)

    wav_path = tmp_path / "test_track.wav"
    sf.write(wav_path, audio, sr, subtype="FLOAT")

    analysis = analyze_track(wav_path)

    assert isinstance(analysis, TrackAnalysis)
    assert analysis.path == wav_path
    assert analysis.sample_rate == sr
    assert abs(analysis.bpm - bpm) <= 1.0
    assert len(analysis.beat_times) > 0
    assert len(analysis.downbeat_times) > 0
    assert analysis.meter == 4


def test_downbeat_intervals_vary_with_drift():
    """Generate a click track with deliberate tempo drift (accelerando) and verify
    that onset-refined downbeat intervals are NOT all identical."""
    sr = 44100
    duration_s = 10.0
    num_samples = int(sr * duration_s)
    audio = np.zeros(num_samples, dtype=np.float32)

    click_dur = int(0.01 * sr)
    t_click = np.linspace(0, 0.01, click_dur, endpoint=False)
    click = (np.sin(2 * np.pi * 1000 * t_click) * np.exp(-t_click * 300)).astype(np.float32)

    # Accelerando from 120 to 130 BPM over 10 seconds
    pos = 0.0
    while pos < duration_s - 0.02:
        frac = pos / duration_s
        current_bpm = 120.0 + 10.0 * frac
        sample_pos = int(pos * sr)
        if sample_pos + click_dur < num_samples:
            audio[sample_pos : sample_pos + click_dur] += click
        pos += 60.0 / current_bpm

    # Use average BPM for grid generation
    avg_bpm = 125.0
    _beat_times, downbeat_times = generate_beat_grid(audio, sr, avg_bpm, meter=4)

    assert len(downbeat_times) >= 3
    intervals = [downbeat_times[i + 1] - downbeat_times[i] for i in range(len(downbeat_times) - 1)]
    # With onset refinement, intervals should NOT all be identical
    unique_intervals = {round(iv, 6) for iv in intervals}
    assert len(unique_intervals) > 1, f"All intervals identical: {intervals}"
