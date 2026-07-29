def calculate_frame_alignment(duration_s: float, fps: int) -> tuple[int, float, bool]:
    """Calculate frame count, residual drift in ms, and sub-frame drift status for a duration and fps.

    Args:
        duration_s: Exact duration in seconds.
        fps: Frames per second.

    Returns:
        Tuple of (frames, drift_ms, drift_is_subframe).
    """
    if fps <= 0 or duration_s <= 0:
        return 0, 0.0, True

    frames = round(duration_s * fps)
    frame_duration_ms = 1000.0 / fps
    drift_ms = (frames / fps - duration_s) * 1000.0
    drift_is_subframe = abs(drift_ms) < frame_duration_ms

    return frames, round(drift_ms, 2), drift_is_subframe
