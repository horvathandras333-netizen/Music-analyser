from typing import Literal

from models import ClipSpec
from spec.cadence import build_cadence_ladder
from spec.frames import calculate_frame_alignment


def build_clip_spec(
    start_s: float,
    end_s: float,
    bpm: float,
    fps: int = 24,
    meter: int = 4,
    loop_mode: Literal["ping_pong", "true_cycle"] = "ping_pong",
    downbeat_times: list[float] | None = None,
) -> ClipSpec:
    """Build a complete ClipSpec model from region selection and BPM.

    Args:
        start_s: Region start time in seconds.
        end_s: Region end time in seconds.
        bpm: Beats per minute.
        fps: Target frame rate (default 24).
        meter: Beats per bar (default 4).
        loop_mode: Loop mode preference ("ping_pong" or "true_cycle").
        downbeat_times: Optional list of detected downbeat timestamps.

    Returns:
        Populated ClipSpec Pydantic model.
    """
    raw_duration = max(0.0, end_s - start_s)
    beat_period = 60.0 / bpm if bpm > 0 else 0.5
    bar_period = beat_period * meter
    beats = max(1, round(raw_duration / beat_period))
    bars = beats / meter

    # Calculate measured duration using downbeat_times if provided
    if downbeat_times and len(downbeat_times) > 0:
        # Find index of downbeat closest to start_s
        start_idx = min(range(len(downbeat_times)), key=lambda i: abs(downbeat_times[i] - start_s))
        end_idx = start_idx + round(bars)
        if end_idx < len(downbeat_times):
            measured_end_s = downbeat_times[end_idx]
        else:
            extra_bars = end_idx - (len(downbeat_times) - 1)
            measured_end_s = downbeat_times[-1] + extra_bars * bar_period
        duration_s = max(0.0, measured_end_s - start_s)
    else:
        duration_s = raw_duration

    arithmetic_duration_s = beats * beat_period
    tempo_drift_ms = round((duration_s - arithmetic_duration_s) * 1000.0, 1)

    frames, drift_ms, drift_is_subframe = calculate_frame_alignment(duration_s, fps)
    cadence = build_cadence_ladder(bpm, beats, meter=meter)

    return ClipSpec(
        start_s=round(start_s, 3),
        end_s=round(start_s + duration_s, 3),
        beats=beats,
        bars=round(bars, 3),
        duration_s=round(duration_s, 3),
        fps=fps,
        frames=frames,
        drift_ms=drift_ms,
        drift_is_subframe=drift_is_subframe,
        tempo_drift_ms=tempo_drift_ms,
        loop_mode=loop_mode,
        cadence=cadence,
    )
