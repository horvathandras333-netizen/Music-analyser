from models import ClipSpec, TrackAnalysis
from spec.candidates import enumerate_candidates
from spec.loopmode import get_loop_mode_advisory


def _format_bars(bars: float) -> str:
    """Format bar count without lossy rounding. Integer bars get no decimal."""
    if abs(bars - round(bars)) < 1e-4:
        return str(round(bars))
    return f"{bars:.4g}"


def render_report(
    analysis: TrackAnalysis,
    spec: ClipSpec,
    candidates: list[tuple[int, float, float]] | None = None,
    target_duration_s: float | None = None,
    style: str = "default",
) -> str:
    """Render ClipSpec and TrackAnalysis into a copy-ready plain text block.

    Args:
        analysis: Populated TrackAnalysis model.
        spec: Populated ClipSpec model.
        candidates: Optional list of ranked candidates (beats, bars, duration_s).
        target_duration_s: The user's original target duration for ranking.
        style: Fragment style name (default: "default").

    Returns:
        Formatted multi-line text block string.
    """
    first_downbeat = analysis.downbeat_times[0] if analysis.downbeat_times else 0.0
    beat_period = 60.0 / analysis.bpm if analysis.bpm > 0 else 0.5
    bar_period = beat_period * analysis.meter

    # Bar numbers calculated relative to the first detected downbeat (= Bar 1)
    # end_bar is inclusive: a 4-bar region starting at bar 1 is "bars 1-4"
    start_bar = max(1, round((spec.start_s - first_downbeat) / bar_period) + 1)
    end_bar = start_bar + round(spec.bars) - 1

    if analysis.bpm_confidence < 0.85 and analysis.bpm_alternates:
        alts_str = ", ".join(f"{alt:.2f}" for alt in analysis.bpm_alternates)
        bpm_info = f"BPM: {analysis.bpm:.2f} (confidence {analysis.bpm_confidence:.2f}, alternates: {alts_str})"
    else:
        bpm_info = f"BPM: {analysis.bpm:.2f} (confidence {analysis.bpm_confidence:.2f})"

    drift_sign = "+" if spec.drift_ms >= 0 else ""
    drift_str = f"{drift_sign}{round(spec.drift_ms)}ms"

    # Effective duration computed from frames, not ideal duration
    frame_aligned_duration = spec.frames / spec.fps if spec.fps > 0 else spec.duration_s
    if spec.loop_mode == "ping_pong":
        effective_frames = 2 * spec.frames
    else:
        effective_frames = spec.frames
    effective_dur = effective_frames / spec.fps if spec.fps > 0 else spec.duration_s

    # Sub-frame check applied to effective duration
    frame_duration_ms = 1000.0 / spec.fps if spec.fps > 0 else 41.67
    effective_drift_ms = (effective_dur - (spec.duration_s * (2.0 if spec.loop_mode == "ping_pong" else 1.0))) * 1000.0
    subframe_str = ", sub-frame" if abs(effective_drift_ms) < frame_duration_ms else ""

    tempo_drift_sign = "+" if spec.tempo_drift_ms >= 0 else ""
    tempo_drift_str = f"{tempo_drift_sign}{spec.tempo_drift_ms:.1f}ms"

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

    # Prompt fragment uses frame-aligned duration and mode-appropriate pose language
    accent1 = beat_period
    accent2 = beat_period * 3.0
    if spec.loop_mode == "true_cycle":
        pose_line = (
            f"Pose at {frame_aligned_duration:.2f}s is identical to pose at\n"
            f"0.00s. Seamlessly loopable. {spec.fps}fps."
        )
    else:
        pose_line = (
            "End at the extreme of the movement; do not return to the opening pose.\n"
            f"Seamlessly loopable via ping-pong reversal. {spec.fps}fps."
        )

    prompt_fragment = (
        "Static locked-off camera, no drift or push. Subject completes one full\n"
        f"weight-shift every {recommended_interval:.2f} seconds, with a sharp shoulder accent at {accent1:.2f}s "
        f"and {accent2:.2f}s within each cycle. {pose_line}"
    )

    # Candidates ranked against target, not selected region
    effective_target = target_duration_s if target_duration_s is not None else spec.duration_s
    if candidates is None:
        candidates = enumerate_candidates(analysis.bpm, target_duration_s=effective_target, meter=analysis.meter)

    top_candidates = candidates[:3] if candidates else []
    candidate_lines: list[str] = []
    for idx, (c_beats, c_bars, c_dur) in enumerate(top_candidates, 1):
        selected_tag = " [selected]" if c_beats == spec.beats else ""
        c_eff = c_dur * 2.0 if spec.loop_mode == "ping_pong" else c_dur
        bars_str = _format_bars(c_bars)
        candidate_lines.append(
            f"  #{idx}: {c_beats} beats ({bars_str} bars, {c_dur:.3f}s, eff {c_eff:.3f}s){selected_tag}"
        )

    # Advisory only for ping_pong; true_cycle gets its own advisory
    advisory_text = get_loop_mode_advisory(spec.loop_mode)

    bars_display = _format_bars(spec.bars)
    target_line = f"Target: {effective_target:.1f}s" if target_duration_s is not None else ""

    lines = [
        f"TRACK: {analysis.path.name}",
        f"{bpm_info} | Meter: {analysis.meter}/4 | First downbeat: {first_downbeat:.3f}s",
        f"SELECTED REGION: {spec.start_s:.3f}s - {spec.end_s:.3f}s (bars {start_bar}-{end_bar})",
    ]
    if target_line:
        lines.append(target_line)
    lines += [
        "",
        "CLIP SPEC",
        f"Duration: {spec.duration_s:.3f}s ({spec.beats} beats / {bars_display} bars) [tempo drift: {tempo_drift_str}]",
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
