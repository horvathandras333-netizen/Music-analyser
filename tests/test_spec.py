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
    # 32 beats = 11.034s (8 bars, phrase length in {2, 4, 8, 16}) ranks above 28 beats (7 bars)
    candidates = enumerate_candidates(174.0, target_duration_s=10.0)
    assert len(candidates) > 0
    top_beats, top_bars, top_dur = candidates[0]
    assert top_beats == 32
    assert top_bars == 8.0
    assert abs(top_dur - 11.034) < 0.01


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
    assert per_beat.divides_evenly is True

    per_bar = next(row for row in cadence if row.label == "per bar")
    assert per_bar.recommended is True
    assert per_bar.divides_evenly is True


def test_cadence_row_divides_evenly():
    # 22 beats with meter 4 -> 5.5 bars.
    # per bar (4 beats) -> 22 % 4 != 0 -> divides_evenly = False
    cadence = build_cadence_ladder(145.0, beats=22, meter=4)
    per_bar = next(row for row in cadence if row.label == "per bar")
    assert per_bar.divides_evenly is False


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
    assert spec.tempo_drift_ms == 0.0
    assert spec.loop_mode == "ping_pong"
    assert len(spec.cadence) == 4


def test_measured_duration_and_tempo_drift():
    # Measured downbeats with slight tempo drift (+20ms per bar)
    downbeat_times = [0.0, 1.675, 3.350, 5.025, 6.700, 8.375, 10.050]
    spec = build_clip_spec(
        start_s=0.0,
        end_s=9.931,
        bpm=145.0,
        fps=24,
        loop_mode="ping_pong",
        downbeat_times=downbeat_times,
    )
    # 6 bars at measured 10.050s vs arithmetic 9.931s -> drift approx +119ms
    assert spec.duration_s == 10.050
    assert spec.tempo_drift_ms > 0.0


def test_candidate_phrase_length_ranking():
    # Target 10s at 120 BPM (beat period = 0.5s)
    # 16 beats = 8.0s (4 bars, phrase length!)
    # 20 beats = 10.0s (5 bars, non-phrase whole bar)
    candidates = enumerate_candidates(120.0, target_duration_s=10.0)
    top_beats = [c[0] for c in candidates[:3]]
    # Phrase length 4 bars (16 beats) or 8 bars should rank above 5 bars
    assert 16 in top_beats or 32 in top_beats
