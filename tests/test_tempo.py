import numpy as np
import pytest

from analysis.tempo import compute_spectral_flux, estimate_tempo


def generate_click_track(bpm: float, sample_rate: int = 44100, duration_s: float = 12.0) -> np.ndarray:
    """Generate a synthetic click track at the specified BPM."""
    num_samples = int(sample_rate * duration_s)
    audio = np.zeros(num_samples, dtype=np.float32)
    beat_interval_samples = int(sample_rate * (60.0 / bpm))

    click_duration = int(0.01 * sample_rate)
    t_click = np.linspace(0, 0.01, click_duration, endpoint=False)
    click = (np.sin(2 * np.pi * 1000 * t_click) * np.exp(-t_click * 300)).astype(np.float32)

    for pos in range(0, num_samples - click_duration, beat_interval_samples):
        audio[pos : pos + click_duration] += click

    return audio


@pytest.mark.parametrize("target_bpm", [90.0, 128.0, 145.0, 174.0])
def test_estimate_tempo_synthetic_clicks(target_bpm: float):
    sr = 44100
    audio = generate_click_track(target_bpm, sample_rate=sr, duration_s=12.0)

    bpm, confidence, alternates = estimate_tempo(audio, sr)

    assert abs(bpm - target_bpm) <= 1.0, f"Expected {target_bpm} ± 1.0, got {bpm}"
    assert 0.0 <= confidence <= 1.0
    assert len(alternates) == 2
    assert alternates[0] == pytest.approx(bpm / 2.0, abs=0.1)
    assert alternates[1] == pytest.approx(bpm * 2.0, abs=0.1)


def test_estimate_tempo_short_audio():
    sr = 44100
    short_audio = np.zeros(100, dtype=np.float32)
    bpm, confidence, _alternates = estimate_tempo(short_audio, sr)
    assert bpm == 120.0
    assert confidence == 0.0


def test_compute_spectral_flux_shape():
    sr = 44100
    audio = generate_click_track(120.0, sample_rate=sr, duration_s=2.0)
    flux = compute_spectral_flux(audio, sr)
    assert flux.ndim == 1
    assert len(flux) > 0
