from models import CadenceRow


def build_cadence_ladder(bpm: float, beats: int, meter: int = 4) -> list[CadenceRow]:
    """Build cadence ladder for subdivisions (per beat, per 2 beats, per bar, per 2 bars).

    Args:
        bpm: Beats per minute.
        beats: Total beat count in the clip.
        meter: Beats per bar (default 4).

    Returns:
        List of CadenceRow models.
    """
    if bpm <= 0 or beats <= 0:
        return []

    beat_period = 60.0 / bpm
    subdivisions = [
        ("per beat", 1),
        ("per 2 beats", 2),
        ("per bar", meter),
        ("per 2 bars", meter * 2),
    ]

    cadence: list[CadenceRow] = []
    for label, sub_beats in subdivisions:
        interval_s = sub_beats * beat_period
        gestures_in_clip = beats / sub_beats
        recommended = 0.9 <= interval_s <= 2.2
        divides_evenly = (beats % sub_beats == 0)
        cadence.append(
            CadenceRow(
                label=label,
                interval_s=round(interval_s, 3),
                gestures_in_clip=round(gestures_in_clip, 1),
                recommended=recommended,
                divides_evenly=divides_evenly,
            )
        )

    return cadence
