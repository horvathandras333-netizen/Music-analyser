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

    candidate_beats_set = set(range(min_beats, max_beats + 1))

    # Also include phrase-length bar counts ({2, 4, 8, 16} bars) within +/-25% of target duration
    phrase_min_beats = max(1, math.ceil((target_duration_s * 0.75) / beat_period))
    phrase_max_beats = math.floor((target_duration_s * 1.25) / beat_period)
    for b in range(phrase_min_beats, phrase_max_beats + 1):
        bars = b / meter
        if b % meter == 0 and round(bars) in {2, 4, 8, 16} and abs(bars - round(bars)) < 1e-4:
            candidate_beats_set.add(b)

    # Also check shorter phrase-length beat counts whose ping-pong duration (2x) lands in target range
    half_target = target_duration_s / 2.0
    half_min_beats = max(1, math.ceil((half_target * (1.0 - max_variance)) / beat_period))
    half_max_beats = math.floor((half_target * (1.0 + max_variance)) / beat_period)
    for b in range(half_min_beats, half_max_beats + 1):
        bars = b / meter
        if b % meter == 0 and round(bars) in {2, 4, 8, 16} and abs(bars - round(bars)) < 1e-4:
            candidate_beats_set.add(b)

    if not candidate_beats_set:
        closest_beats = max(1, round(target_duration_s / beat_period))
        candidate_beats_set.add(closest_beats)

    candidates: list[tuple[int, float, float]] = []
    for b in candidate_beats_set:
        dur = b * beat_period
        bars = b / meter
        candidates.append((b, round(bars, 3), round(dur, 3)))

    def rank_key(c: tuple[int, float, float]) -> tuple[int, float]:
        beats, _, dur = c
        bars = beats / meter
        is_phrase = (beats % meter == 0) and (round(bars) in {2, 4, 8, 16}) and abs(bars - round(bars)) < 1e-4
        is_whole_bar = beats % meter == 0

        # Tier 0: Phrase-aligned bar count (2, 4, 8, 16)
        # Tier 1: Other whole bar count
        # Tier 2: Non-whole bar count
        if is_phrase:
            tier = 0
        elif is_whole_bar:
            tier = 1
        else:
            tier = 2

        # Effective closeness: compare direct duration or 2x ping-pong duration to target
        closeness_direct = abs(dur - target_duration_s)
        closeness_pingpong = abs((dur * 2.0) - target_duration_s)
        closeness = min(closeness_direct, closeness_pingpong)

        return (tier, closeness)

    candidates.sort(key=rank_key)
    return candidates
