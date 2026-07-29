# LoopForge — PLAN.md

**Working name:** LoopForge (fits the ReelForge / WanForge family — rename freely)

## 1. Purpose

Audio file in → tempo and beat grid out → user selects a musically-aligned region → app emits a **copy-ready text block** describing a loop-safe video clip spec, phrased in seconds and plain language so it can be pasted directly into a Gemini/Veo prompt.

The app never talks to a video model. It produces text for a human to paste. That boundary keeps it small and keeps it useful when the video tooling changes.

## 2. Non-goals

- No video rendering, encoding, or ffmpeg output pipeline
- No API calls to Gemini, Veo, or any hosted model
- No stem separation or key detection (v2 candidates)
- No dependency on `reelforge-core` — this is standalone, self-contained detection

## 3. Architecture

```
loopforge/
  models.py            # pydantic v2 models, no logic
  analysis/
    decode.py          # audio → mono float32 numpy array + sample rate
    tempo.py           # spectral flux → onset envelope → autocorrelation → BPM
    grid.py            # beat times, downbeat phase, bar boundaries
  spec/
    candidates.py      # beat-count options near a target duration
    frames.py          # fps alignment, residual drift
    cadence.py         # gesture-per-subdivision ladder
    loopmode.py        # ping-pong vs true-cycle advisory
  report/
    render.py          # ClipSpec → the pasteable text block
  cli.py               # headless entry point
  ui/
    main_window.py     # PySide6 shell
    waveform.py        # custom-painted waveform widget
    spec_panel.py      # read-only spec display + copy button
tests/
```

**Design rule:** everything under `spec/` and `report/` is pure functions over pydantic models — no audio, no Qt, no I/O. These carry the test weight. `analysis/` is thin and integration-tested against generated click tracks. `ui/` holds zero math.

## 4. Data models (pydantic v2)

```
TrackAnalysis
  path: Path
  sample_rate: int
  duration_s: float
  bpm: float
  bpm_confidence: float          # 0..1, from autocorrelation peak sharpness
  bpm_alternates: list[float]    # octave candidates (÷2, ×2) for UI toggle
  beat_times: list[float]
  downbeat_times: list[float]
  meter: int = 4

ClipSpec
  start_s: float
  end_s: float
  beats: int
  bars: float
  duration_s: float
  fps: int
  frames: int                    # rounded
  drift_ms: float                # signed, duration vs frames/fps
  drift_is_subframe: bool
  loop_mode: Literal["ping_pong", "true_cycle"]
  cadence: list[CadenceRow]

CadenceRow
  label: str                     # "per beat", "per bar", "per 2 bars"
  interval_s: float
  gestures_in_clip: float
  recommended: bool              # heuristic: interval in 0.9–2.2s window
```

## 5. Core math — the part that must be right

**Beat-count candidates.** Given BPM and a target duration (default 10.0s), enumerate integer beat counts whose duration falls within ±15% of target. Rank by: whole-bar multiples first, then closeness to target. At 145 BPM and target 10s the winner is 24 beats = 9.931s (6 bars). At 174 BPM it's 28 beats = 9.655s (7 bars).

**Frame alignment.** `frames = round(duration_s * fps)`; `drift_ms = (frames / fps - duration_s) * 1000`. Flag `drift_is_subframe` when `abs(drift_ms) < 1000 / fps`. Report the number always — do not silently round. Some BPM/fps pairs leave drift large enough to break a loop and the user needs to see it.

**Cadence ladder.** For each subdivision (beat, 2 beats, bar, 2 bars), emit interval and gesture count. Mark `recommended` where the interval lands in roughly 0.9–2.2s — the window where human-scale movement reads naturally on screen. At DnB tempos this correctly pushes the recommendation to one gesture per bar rather than per beat.

**Loop mode advisory.** Default `ping_pong` (guarantees a seam-free loop, doubles effective length). Emit a warning alongside it: reversal breaks any motion with a preferred direction — falling hair, rising smoke, drifting particles, anything gravity-driven. For those, `true_cycle` is required and the prompt must instead demand that the final pose match the first.

**BPM octave errors.** Spectral-flux autocorrelation routinely returns half or double the perceived tempo. Resolve with a prior favouring 85–175 BPM, but always populate `bpm_alternates` and expose a ×2 / ÷2 toggle in the UI. Do not hide this behind a confidence score.

**Grid mode.** Two options, user-selectable: *detected* (snap region edges to nearest detected downbeat — correct for humanised or drifting tempo) and *arithmetic* (constant period from first downbeat — correct for programmed tracks). Default to detected.

## 6. Report output — target format

```
TRACK: Sunfire.wav
BPM: 145.02 (confidence 0.91) | Meter: 4/4 | First downbeat: 0.284s
SELECTED REGION: 32.114s - 42.045s (bars 20-26)

CLIP SPEC
Duration: 9.931s (24 beats / 6 bars)
Frames @24fps: 238 (residual drift +14ms, sub-frame)
Loop mode: ping-pong (effective 19.862s)

CADENCE
  per beat    0.414s   x24.0
  per 2 beats 0.828s   x12.0
  per bar     1.655s   x6.0    <- recommended
  per 2 bars  3.310s   x3.0

PROMPT FRAGMENT
Static locked-off camera, no drift or push. Subject completes one full
weight-shift every 1.65 seconds, with a sharp shoulder accent at 0.41s
and 1.24s within each cycle. Pose at 9.93s is identical to pose at
0.00s. Seamlessly loopable. 24fps.

ADVISORY
Ping-pong playback reverses motion. Safe for sways, turns, and breathing.
Not safe for hair fall, smoke, or particles - switch to true-cycle.
```

Renderer takes a `style` argument so the prompt fragment can be swapped without touching the spec math.

## 7. Phases

Each phase ends with: tests green, `ruff check` clean, one commit, then **stop and report**. No phase begins before the previous is approved.

| # | Phase | Done when |
|---|---|---|
| 0 | Scaffold: uv project, ruff, pytest, models.py | `pytest` runs, models validate, zero logic |
| 1 | `analysis/decode.py` | Loads wav/mp3/flac to mono float32; tested on generated tone |
| 2 | `analysis/tempo.py` | BPM within ±1 of truth on synthetic click tracks at 90/128/145/174 |
| 3 | `analysis/grid.py` | Beat and downbeat times; phase offset correct on click tracks |
| 4 | `spec/` all modules | Pure-function unit tests incl. drift edge cases and octave handling |
| 5 | `report/render.py` + `cli.py` | **MVP CHECKPOINT** — `loopforge analyze x.wav --target 10 --fps 24` prints the full block |
| 6 | PySide6 shell + waveform paint | Window opens, file loads, waveform draws, beat ticks overlaid |
| 7 | Drag-select with downbeat snapping | Selection snaps, spec panel updates live |
| 8 | Copy button, fps/target/loop-mode controls, recent files | Round-trip usable without touching the CLI |
| 9 | PyInstaller one-file build | Runs on clean Windows box |

**MVP checkpoint (end of phase 5)** is the real gate. If the CLI produces a correct block for a real track, the project has already delivered its value; the GUI is convenience.

## 8. Stack

Python 3.11+, uv, pytest, ruff, pydantic v2, numpy, soundfile, PySide6. ffmpeg on PATH for formats soundfile won't decode. No librosa — the spectral-flux approach is ~80 lines and avoids the dependency weight.

## 9. Test strategy

Generate click tracks in-process at known BPMs (numpy, impulse train + noise burst) and assert detected BPM, beat count, and downbeat phase. This makes phases 1–3 verifiable without any audio fixtures in the repo. Phases 4–5 are pure-function tests including: drift at awkward fps (29.97, 30, 60), BPM values that yield no whole-bar candidate near target, and single-beat and zero-length selections.

## 10. Open questions

1. Working name — keep LoopForge or something else?
2. Default target duration 10s, or make it a config value from the start given Veo's limit may change?
3. Should the report include a second fragment variant tuned for a different video model, or keep one style and add later?
