from models import ClipSpec, TrackAnalysis
from spec.candidates import enumerate_candidates
from spec.loopmode import get_loop_mode_advisory


def render_report(
    analysis: TrackAnalysis,
    spec: ClipSpec,
    candidates: list[tuple[int, float, float]] | None = None,
    style: str = "default",
) -> str:
    """Render ClipSpec and TrackAnalysis into a copy-ready plain text block.

    Args:
        analysis: Populated TrackAnalysis model.
        spec: Populated ClipSpec model.
        candidates: Optional list of ranked candidates (beats, bars, duration_s).
        style: Fragment style name (default: "default").

    Returns:
        Formatted multi-line text block string.
    """
    first_downbeat = analysis.downbeat_times[0] if analysis.downbeat_times else 0.0
    beat_period = 60.0 / analysis.bpm if analysis.bpm > 0 else 0.5
    bar_period = beat_period * analysis.meter

    # Bar numbers calculated relative to the first detected downbeat (= Bar 1)
    start_bar = max(1, round((spec.start_s - first_downbeat) / bar_period) + 1)
    end_bar = start_bar + round(spec.bars)

    if analysis.bpm_confidence < 0.85 and analysis.bpm_alternates:
        alts_str = ", ".join(f"{alt:.2f}" for alt in analysis.bpm_alternates)
        bpm_info = f"BPM: {analysis.bpm:.2f} (confidence {analysis.bpm_confidence:.2f}, alternates: {alts_str})"
    else:
        bpm_info = f"BPM: {analysis.bpm:.2f} (confidence {analysis.bpm_confidence:.2f})"

    drift_sign = "+" if spec.drift_ms >= 0 else ""
    drift_str = f"{drift_sign}{round(spec.drift_ms)}ms"
    subframe_str = ", sub-frame" if spec.drift_is_subframe else ""

    tempo_drift_sign = "+" if spec.tempo_drift_ms >= 0 else ""
    tempo_drift_str = f"{tempo_drift_sign}{spec.tempo_drift_ms:.1f}ms"

    effective_dur = spec.duration_s * 2.0 if spec.loop_mode == "ping_pong" else spec.duration_s
    loop_mode_formatted = spec.loop_mode.replace("_", "-")

    cadence_lines: list[str] = []
    recommended_interval = spec.duration_s
    for row in spec.cadence:
        rec = "    <- recommended" if row.recommended else ""
        incompat = " (loop-incompatible)" if not row.divides_evenly else ""
        cadence_lines.append(
            f"  {row.label:<11} {row.interval_s:.3f}s   x{row.gestures_in_clip:.1f}{incompat}{rec}"
        )
        if row.recommended and recommended_interval == spec.duration_s:
            recommended_interval = row.interval_s

    accent1 = beat_period
    accent2 = beat_period * 3.0
    prompt_fragment = (
        "Static locked-off camera, no drift or push. Subject completes one full\n"
        f"weight-shift every {recommended_interval:.2f} seconds, with a sharp shoulder accent at {accent1:.2f}s "
        f"and {accent2:.2f}s within each cycle. Pose at {spec.duration_s:.2f}s "
        "is identical to pose at\n"
        f"0.00s. Seamlessly loopable. {spec.fps}fps."
    )

    if candidates is None:
        candidates = enumerate_candidates(analysis.bpm, target_duration_s=spec.duration_s, meter=analysis.meter)

    top_candidates = candidates[:3] if candidates else []
    candidate_lines: list[str] = []
    for idx, (c_beats, c_bars, c_dur) in enumerate(top_candidates, 1):
        selected_tag = " [selected]" if c_beats == spec.beats else ""
        candidate_lines.append(f"  #{idx}: {c_beats} beats ({c_bars:.1f} bars, {c_dur:.3f}s){selected_tag}")

    advisory_text = get_loop_mode_advisory(spec.loop_mode)

    lines = [
        f"TRACK: {analysis.path.name}",
        f"{bpm_info} | Meter: {analysis.meter}/4 | First downbeat: {first_downbeat:.3f}s",
        f"SELECTED REGION: {spec.start_s:.3f}s - {spec.end_s:.3f}s (bars {start_bar}-{end_bar})",
        "",
        "CLIP SPEC",
        f"Duration: {spec.duration_s:.3f}s ({spec.beats} beats / {spec.bars:.1f} bars) [tempo drift: {tempo_drift_str}]",
        f"Frames @{spec.fps}fps: {spec.frames} (residual drift {drift_str}{subframe_str})",
        f"Loop mode: {loop_mode_formatted} (effective {effective_dur:.3f}s)",
        "",
        "TOP CANDIDATES",
        *candidate_lines,
        "",
        "CADENCE",
        *cadence_lines,
        "",
        "PROMPT FRAGMENT",
        prompt_fragment,
        "",
        "ADVISORY",
        advisory_text,
    ]

    return "\n".join(lines)
