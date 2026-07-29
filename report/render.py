from models import ClipSpec, TrackAnalysis
from spec.loopmode import get_loop_mode_advisory


def render_report(analysis: TrackAnalysis, spec: ClipSpec, style: str = "default") -> str:
    """Render ClipSpec and TrackAnalysis into a copy-ready plain text block.

    Args:
        analysis: Populated TrackAnalysis model.
        spec: Populated ClipSpec model.
        style: Fragment style name (default: "default").

    Returns:
        Formatted multi-line text block string.
    """
    first_downbeat = analysis.downbeat_times[0] if analysis.downbeat_times else 0.0
    beat_period = 60.0 / analysis.bpm if analysis.bpm > 0 else 0.5

    start_bar = round(spec.start_s / (beat_period * analysis.meter)) + 1
    end_bar = round(spec.end_s / (beat_period * analysis.meter)) + 1

    drift_sign = "+" if spec.drift_ms >= 0 else ""
    drift_str = f"{drift_sign}{round(spec.drift_ms)}ms"
    subframe_str = ", sub-frame" if spec.drift_is_subframe else ""

    effective_dur = spec.duration_s * 2.0 if spec.loop_mode == "ping_pong" else spec.duration_s
    loop_mode_formatted = spec.loop_mode.replace("_", "-")

    cadence_lines: list[str] = []
    recommended_interval = spec.duration_s
    for row in spec.cadence:
        rec = "    <- recommended" if row.recommended else ""
        cadence_lines.append(
            f"  {row.label:<11} {row.interval_s:.3f}s   x{row.gestures_in_clip:.1f}{rec}"
        )
        if row.recommended and recommended_interval == spec.duration_s:
            recommended_interval = row.interval_s

    prompt_fragment = (
        "Static locked-off camera, no drift or push. Subject completes one full\n"
        f"weight-shift every {recommended_interval:.2f} seconds. Pose at {spec.duration_s:.2f}s "
        "is identical to pose at\n"
        f"0.00s. Seamlessly loopable. {spec.fps}fps."
    )

    advisory_text = get_loop_mode_advisory(spec.loop_mode)

    lines = [
        f"TRACK: {analysis.path.name}",
        f"BPM: {analysis.bpm:.2f} (confidence {analysis.bpm_confidence:.2f}) | Meter: {analysis.meter}/4 | First downbeat: {first_downbeat:.3f}s",
        f"SELECTED REGION: {spec.start_s:.3f}s - {spec.end_s:.3f}s (bars {start_bar}-{end_bar})",
        "",
        "CLIP SPEC",
        f"Duration: {spec.duration_s:.3f}s ({spec.beats} beats / {spec.bars:.1f} bars)",
        f"Frames @{spec.fps}fps: {spec.frames} (residual drift {drift_str}{subframe_str})",
        f"Loop mode: {loop_mode_formatted} (effective {effective_dur:.3f}s)",
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
