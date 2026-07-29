from pathlib import Path

import pytest
from pydantic import ValidationError

from models import CadenceRow, ClipSpec, TrackAnalysis


def test_cadence_row_validation():
    row = CadenceRow(
        label="per bar",
        interval_s=1.655,
        gestures_in_clip=6.0,
        recommended=True,
    )
    assert row.label == "per bar"
    assert row.interval_s == 1.655
    assert row.gestures_in_clip == 6.0
    assert row.recommended is True


def test_clip_spec_validation():
    cadence = [
        CadenceRow(
            label="per bar",
            interval_s=1.655,
            gestures_in_clip=6.0,
            recommended=True,
        )
    ]
    spec = ClipSpec(
        start_s=32.114,
        end_s=42.045,
        beats=24,
        bars=6.0,
        duration_s=9.931,
        fps=24,
        frames=238,
        drift_ms=14.0,
        drift_is_subframe=True,
        loop_mode="ping_pong",
        cadence=cadence,
    )
    assert spec.duration_s == 9.931
    assert spec.loop_mode == "ping_pong"
    assert len(spec.cadence) == 1

    with pytest.raises(ValidationError):
        ClipSpec(
            start_s=0.0,
            end_s=10.0,
            beats=24,
            bars=6.0,
            duration_s=10.0,
            fps=24,
            frames=240,
            drift_ms=0.0,
            drift_is_subframe=True,
            loop_mode="invalid_mode",  # type: ignore
            cadence=[],
        )


def test_track_analysis_validation():
    analysis = TrackAnalysis(
        path=Path("audio/test.wav"),
        sample_rate=44100,
        duration_s=60.0,
        bpm=145.0,
        bpm_confidence=0.91,
        bpm_alternates=[72.5, 290.0],
        beat_times=[0.0, 0.414, 0.828],
        downbeat_times=[0.0, 1.655],
        meter=4,
    )
    assert analysis.bpm == 145.0
    assert analysis.meter == 4
    assert len(analysis.bpm_alternates) == 2

    with pytest.raises(ValidationError):
        TrackAnalysis(
            path=Path("audio/test.wav"),
            sample_rate=44100,
            duration_s=60.0,
            bpm=145.0,
            bpm_confidence=1.5,  # Out of range 0..1
            bpm_alternates=[],
            beat_times=[],
            downbeat_times=[],
        )
