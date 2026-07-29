import math


def enumerate_candidates(
    bpm: float,
    target_duration_s: float = 10.0,
    max_variance: float = 0.15,
    meter: int = 4,
) -> list[tuple[int, float, float]]:
    """Enumerate candidate beat counts near a target duration.

    Args:
        bpm: Beats per minute.
        target_duration_s: Target clip duration in seconds.
        max_variance: Allowed relative variance from target duration (default ±15%).
        meter: Number of beats per bar (default 4).

    Returns:
        List of tuples (beats, bars, duration_s) ranked by whole-bar multiples first,
        then closeness to target duration.
    """
    if bpm <= 0 or target_duration_s <= 0:
        return []

    beat_period = 60.0 / bpm
    min_duration = target_duration_s * (1.0 - max_variance)
    max_duration = target_duration_s * (1.0 + max_variance)

    min_beats = max(1, math.ceil(min_duration / beat_period))
    max_beats = math.floor(max_duration / beat_period)

    if min_beats > max_beats:
        # Fallback to closest integer beats if window is too tight
        closest_beats = max(1, round(target_duration_s / beat_period))
        candidates_raw = [closest_beats]
    else:
        candidates_raw = list(range(min_beats, max_beats + 1))

    candidates: list[tuple[int, float, float]] = []
    for b in candidates_raw:
        dur = b * beat_period
        bars = b / meter
        candidates.append((b, round(bars, 3), round(dur, 3)))

    def rank_key(c: tuple[int, float, float]) -> tuple[bool, float]:
        beats, _, dur = c
        is_whole_bar = beats % meter == 0
        closeness = abs(dur - target_duration_s)
        return (not is_whole_bar, closeness)

    candidates.sort(key=rank_key)
    return candidates
