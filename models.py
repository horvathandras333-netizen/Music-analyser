from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class CadenceRow(BaseModel):
    label: str
    interval_s: float
    gestures_in_clip: float
    recommended: bool
    divides_evenly: bool


class ClipSpec(BaseModel):
    start_s: float
    end_s: float
    beats: int
    bars: float
    duration_s: float
    fps: int
    frames: int
    drift_ms: float
    drift_is_subframe: bool
    tempo_drift_ms: float
    loop_mode: Literal["ping_pong", "true_cycle"]
    cadence: list[CadenceRow]


class TrackAnalysis(BaseModel):
    path: Path
    sample_rate: int
    duration_s: float
    bpm: float
    bpm_confidence: float = Field(ge=0.0, le=1.0)
    bpm_alternates: list[float]
    beat_times: list[float]
    downbeat_times: list[float]
    meter: int = 4
