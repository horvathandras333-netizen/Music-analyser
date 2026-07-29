from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from analysis.decode import load_audio


def test_load_audio_mono_wav(tmp_path: Path):
    sr = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
    tone = np.sin(2 * np.pi * 440 * t).astype(np.float32)

    wav_file = tmp_path / "mono.wav"
    sf.write(wav_file, tone, sr, subtype="FLOAT")

    samples, sample_rate = load_audio(wav_file)

    assert sample_rate == sr
    assert samples.dtype == np.float32
    assert samples.ndim == 1
    assert samples.shape[0] == int(sr * duration)
    np.testing.assert_allclose(samples, tone, atol=1e-5)


def test_load_audio_pcm16_wav(tmp_path: Path):
    sr = 44100
    duration = 0.5
    t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
    tone = np.sin(2 * np.pi * 440 * t).astype(np.float32)

    wav_file = tmp_path / "pcm16.wav"
    sf.write(wav_file, tone, sr, subtype="PCM_16")

    samples, sample_rate = load_audio(wav_file)

    assert sample_rate == sr
    assert samples.dtype == np.float32
    assert samples.ndim == 1
    np.testing.assert_allclose(samples, tone, atol=1e-4)


def test_load_audio_stereo_wav(tmp_path: Path):
    sr = 44100
    duration = 0.5
    t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
    left = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    right = np.sin(2 * np.pi * 880 * t).astype(np.float32)
    stereo = np.column_stack((left, right))

    wav_file = tmp_path / "stereo.wav"
    sf.write(wav_file, stereo, sr, subtype="FLOAT")

    samples, sample_rate = load_audio(wav_file)

    assert sample_rate == sr
    assert samples.dtype == np.float32
    assert samples.ndim == 1
    expected_mono = (left + right) / 2.0
    np.testing.assert_allclose(samples, expected_mono, atol=1e-5)


def test_load_audio_missing_file(tmp_path: Path):
    missing_file = tmp_path / "non_existent.wav"
    with pytest.raises(FileNotFoundError):
        load_audio(missing_file)


def test_load_audio_empty_file(tmp_path: Path):
    empty_file = tmp_path / "empty.wav"
    sf.write(empty_file, np.array([], dtype=np.float32), 44100)
    with pytest.raises(ValueError):
        load_audio(empty_file)
