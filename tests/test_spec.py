from spec.builder import build_clip_spec
from spec.cadence import build_cadence_ladder
from spec.candidates import enumerate_candidates
from spec.frames import calculate_frame_alignment
from spec.loopmode import PING_PONG_ADVISORY, TRUE_CYCLE_ADVISORY, get_loop_mode_advisory


def test_enumerate_candidates_145_bpm():
    # At 145 BPM, 10s target -> beat period = 0.41379s.
    # 24 beats = 9.931s (6 bars)
    candidates = enumerate_candidates(145.0, target_duration_s=10.0)
    assert len(candidates) > 0
    top_beats, top_bars, top_dur = candidates[0]
    assert top_beats == 24
    assert top_bars == 6.0
    assert abs(top_dur - 9.931) < 0.01


def test_enumerate_candidates_174_bpm():
    # At 174 BPM, 10s target -> beat period = 0.3448s.
    # 28 beats = 9.655s (7 bars)
    candidates = enumerate_candidates(174.0, target_duration_s=10.0)
    assert len(candidates) > 0
    top_beats, top_bars, top_dur = candidates[0]
    assert top_beats == 28
    assert top_bars == 7.0
    assert abs(top_dur - 9.655) < 0.01


def test_frame_alignment_and_drift():
    # 9.931s at 24fps -> 238.344 frames -> round to 238 frames.
    # 238 / 24 = 9.91667s. Drift = (9.91667 - 9.931) * 1000 = -14.33ms
    frames, drift_ms, drift_sub = calculate_frame_alignment(9.931, 24)
    assert frames == 238
    assert abs(drift_ms - (-14.33)) < 0.5
    assert drift_sub is True  # 1000 / 24 = 41.67ms > 14.33ms

    # Test awkward fps 29.97
    frames_29, drift_29, _ = calculate_frame_alignment(10.0, 30)
    assert frames_29 == 300
    assert drift_29 == 0.0


def test_cadence_ladder_dnb_174_bpm():
    # At 174 BPM, beat period = 0.3448s.
    # per beat = 0.345s (not recommended)
    # per bar = 1.379s (recommended!)
    cadence = build_cadence_ladder(174.0, beats=28, meter=4)
    assert len(cadence) == 4

    per_beat = next(row for row in cadence if row.label == "per beat")
    assert per_beat.recommended is False

    per_bar = next(row for row in cadence if row.label == "per bar")
    assert per_bar.recommended is True


def test_loopmode_advisory():
    assert get_loop_mode_advisory("ping_pong") == PING_PONG_ADVISORY
    assert get_loop_mode_advisory("true_cycle") == TRUE_CYCLE_ADVISORY


def test_build_clip_spec_integration():
    spec = build_clip_spec(start_s=32.114, end_s=42.045, bpm=145.0, fps=24, loop_mode="ping_pong")
    assert spec.beats == 24
    assert spec.bars == 6.0
    assert spec.duration_s == 9.931
    assert spec.fps == 24
    assert spec.frames == 238
    assert spec.loop_mode == "ping_pong"
    assert len(spec.cadence) == 4
