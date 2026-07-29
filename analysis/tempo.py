import numpy as np


def compute_spectral_flux(
    audio: np.ndarray, sample_rate: int, frame_size: int = 2048, hop_size: int = 512
) -> np.ndarray:
    """Compute half-wave rectified spectral flux from consecutive STFT magnitude frames."""
    if len(audio) < frame_size:
        return np.zeros(0, dtype=np.float32)

    window = np.hanning(frame_size).astype(np.float32)
    num_frames = 1 + (len(audio) - frame_size) // hop_size
    frames = np.lib.stride_tricks.sliding_window_view(
        audio[: num_frames * hop_size + frame_size - hop_size], frame_size
    )[::hop_size]

    fft_mag = np.abs(np.fft.rfft(frames * window, axis=1))

    diff = np.diff(fft_mag, axis=0)
    flux = np.sum(np.maximum(0.0, diff), axis=1)

    if len(flux) > 0:
        flux = flux - np.mean(flux)
        flux = np.maximum(0.0, flux)

    return flux.astype(np.float32)


def estimate_tempo(audio: np.ndarray, sample_rate: int) -> tuple[float, float, list[float]]:
    """Estimate tempo (BPM), confidence, and octave alternate BPMs using spectral flux autocorrelation.

    Args:
        audio: 1D float32 mono audio array.
        sample_rate: Sampling rate of the audio in Hz.

    Returns:
        Tuple of (bpm, confidence, bpm_alternates).
    """
    frame_size = 2048
    hop_size = 512
    flux = compute_spectral_flux(audio, sample_rate, frame_size=frame_size, hop_size=hop_size)

    if len(flux) < 10:
        return 120.0, 0.0, [60.0, 240.0]

    fps = sample_rate / hop_size

    n = len(flux)
    autocorr = np.correlate(flux, flux, mode="full")[n - 1 :]
    if autocorr[0] > 0:
        autocorr = autocorr / autocorr[0]

    min_bpm, max_bpm = 50.0, 250.0
    min_lag = max(1, int(fps * 60.0 / max_bpm))
    max_lag = min(len(autocorr) - 2, int(fps * 60.0 / min_bpm))

    if min_lag >= max_lag:
        return 120.0, 0.0, [60.0, 240.0]

    lags = np.arange(min_lag, max_lag + 1)
    bpms = 60.0 * fps / lags

    # Prior favouring 85–175 BPM
    prior_center = 130.0
    prior_sigma = 50.0
    prior = np.exp(-0.5 * ((bpms - prior_center) / prior_sigma) ** 2)

    raw_scores = autocorr[lags]
    scores = raw_scores * prior

    # Find candidate peaks (local maxima in scores)
    peak_indices = []
    for i in range(len(scores)):
        prev_val = scores[i - 1] if i > 0 else scores[i]
        next_val = scores[i + 1] if i < len(scores) - 1 else scores[i]
        if scores[i] >= prev_val and scores[i] >= next_val and scores[i] > 0:
            peak_indices.append(i)

    if not peak_indices:
        best_idx = int(np.argmax(scores))
    else:
        # Sort peak indices by score descending
        peak_indices.sort(key=lambda idx: scores[idx], reverse=True)
        best_idx = peak_indices[0]

        # Check if a shorter lag (higher BPM candidate) has strong raw autocorrelation
        max_raw = raw_scores[best_idx]
        for candidate_idx in peak_indices:
            candidate_lag = lags[candidate_idx]
            if (
                candidate_lag < lags[best_idx]
                and raw_scores[candidate_idx] >= 0.6 * max_raw
                and 80.0 <= bpms[candidate_idx] <= 200.0
            ):
                best_idx = candidate_idx
                break

    best_lag = lags[best_idx]

    # Quadratic interpolation around best_lag for sub-frame accuracy
    if 0 < best_lag < len(autocorr) - 1:
        y1, y2, y3 = autocorr[best_lag - 1], autocorr[best_lag], autocorr[best_lag + 1]
        denom = y1 - 2 * y2 + y3
        if abs(denom) > 1e-7:
            delta = 0.5 * (y1 - y3) / denom
            exact_lag = best_lag + delta
        else:
            exact_lag = float(best_lag)
    else:
        exact_lag = float(best_lag)

    detected_bpm = float(60.0 * fps / exact_lag)

    peak_val = autocorr[best_lag]
    mean_val = float(np.mean(autocorr[lags]))
    confidence = float(np.clip((peak_val - mean_val) / (1.0 - mean_val + 1e-5), 0.0, 1.0))

    bpm_alternates = [round(detected_bpm / 2.0, 2), round(detected_bpm * 2.0, 2)]

    return round(detected_bpm, 2), round(confidence, 2), bpm_alternates
