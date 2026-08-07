from pathlib import Path

import numpy as np

from analysis.decode import load_audio
from analysis.tempo import compute_spectral_flux, estimate_tempo
from models import TrackAnalysis


def find_beat_phase(
    flux: np.ndarray, sample_rate: int, bpm: float, hop_size: int = 512
) -> float:
    """Find the start phase offset in seconds for a given BPM on a spectral flux envelope."""
    if len(flux) == 0 or bpm <= 0:
        return 0.0

    fps = sample_rate / hop_size
    beat_period_frames = (60.0 / bpm) * fps
    period_int = max(1, round(beat_period_frames))

    best_phase = 0
    max_score = -1.0

    for phase in range(min(period_int, len(flux))):
        indices = np.arange(phase, len(flux), period_int)
        score = float(np.sum(flux[indices]))
        if score > max_score:
            max_score = score
            best_phase = phase

    start_phase_s = float(best_phase / fps)
    beat_period_s = 60.0 / bpm

    while start_phase_s >= beat_period_s:
        start_phase_s -= beat_period_s

    return round(start_phase_s, 4)


def generate_beat_grid(
    audio: np.ndarray, sample_rate: int, bpm: float, meter: int = 4, hop_size: int = 512
) -> tuple[list[float], list[float]]:
    """Generate beat_times and downbeat_times arrays for given audio and BPM."""
    duration_s = len(audio) / sample_rate
    beat_period = 60.0 / bpm

    flux = compute_spectral_flux(audio, sample_rate, hop_size=hop_size)
    start_phase = find_beat_phase(flux, sample_rate, bpm, hop_size=hop_size)

    fps = sample_rate / hop_size
    half_period = beat_period / 2.0

    # Generate beat times with onset-peak refinement: for each arithmetic
    # position, search for the nearest spectral-flux peak within ±half a beat
    # period and snap to it. This gives real, per-beat timestamps that drift
    # with the performance rather than tautological arithmetic intervals.
    beat_times: list[float] = []
    current_time = start_phase
    while current_time < duration_s:
        search_start = max(0, int((current_time - half_period) * fps))
        search_end = min(len(flux) - 1, int((current_time + half_period) * fps))
        if search_start < search_end < len(flux):
            window = flux[search_start : search_end + 1]
            peak_offset = int(np.argmax(window))
            refined_time = (search_start + peak_offset) / fps
            # Only accept the refinement if it's within half a beat of the expected position
            if abs(refined_time - current_time) <= half_period:
                beat_times.append(round(refined_time, 6))
            else:
                beat_times.append(round(current_time, 6))
        else:
            beat_times.append(round(current_time, 6))
        current_time += beat_period

    if not beat_times:
        return [], []

    # Determine downbeat phase (0..meter-1)
    best_downbeat_offset = 0
    max_downbeat_score = -1.0

    for offset in range(min(meter, len(beat_times))):
        score = 0.0
        for idx in range(offset, len(beat_times), meter):
            t = beat_times[idx]
            frame_idx = round(t * fps)
            if 0 <= frame_idx < len(flux):
                score += float(flux[frame_idx])
        if score > max_downbeat_score:
            max_downbeat_score = score
            best_downbeat_offset = offset

    downbeat_times = beat_times[best_downbeat_offset::meter]

    return beat_times, downbeat_times


def analyze_track(path: str | Path, meter: int = 4) -> TrackAnalysis:
    """Analyze an audio file and return a populated TrackAnalysis model."""
    file_path = Path(path)
    audio, sr = load_audio(file_path)
    duration_s = len(audio) / sr

    bpm, confidence, alternates = estimate_tempo(audio, sr)
    beat_times, downbeat_times = generate_beat_grid(audio, sr, bpm, meter=meter)

    return TrackAnalysis(
        path=file_path,
        sample_rate=sr,
        duration_s=round(duration_s, 3),
        bpm=bpm,
        bpm_confidence=confidence,
        bpm_alternates=alternates,
        beat_times=beat_times,
        downbeat_times=downbeat_times,
        meter=meter,
    )
