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
) -> ClipSpec:
    """Build a complete ClipSpec model from region selection and BPM.

    Args:
        start_s: Region start time in seconds.
        end_s: Region end time in seconds.
        bpm: Beats per minute.
        fps: Target frame rate (default 24).
        meter: Beats per bar (default 4).
        loop_mode: Loop mode preference ("ping_pong" or "true_cycle").

    Returns:
        Populated ClipSpec Pydantic model.
    """
    duration_s = max(0.0, end_s - start_s)
    beat_period = 60.0 / bpm if bpm > 0 else 0.5
    beats = max(1, round(duration_s / beat_period))
    bars = beats / meter

    frames, drift_ms, drift_is_subframe = calculate_frame_alignment(duration_s, fps)
    cadence = build_cadence_ladder(bpm, beats, meter=meter)

    return ClipSpec(
        start_s=round(start_s, 3),
        end_s=round(end_s, 3),
        beats=beats,
        bars=round(bars, 3),
        duration_s=round(duration_s, 3),
        fps=fps,
        frames=frames,
        drift_ms=drift_ms,
        drift_is_subframe=drift_is_subframe,
        loop_mode=loop_mode,
        cadence=cadence,
    )
