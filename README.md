# LoopForge

**LoopForge** is a Python application and GUI tool that analyzes audio files, detects tempo and beat grids, and generates **copy-ready text specifications for loop-safe video clips**. The output text is phrased in seconds, frame counts, and plain language so it can be pasted directly into video generation models like Gemini / Veo.

![LoopForge CLI & GUI](https://img.shields.io/badge/Python-3.11%2B-blue.svg)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)
![License](https://img.shields.io/badge/license-MIT-purple.svg)

---

## 🎯 Purpose

When generating loopable video clips with AI models (e.g. Gemini / Veo), video duration must align perfectly with musical bars and subdivisions to prevent visible seams or jarring cuts. 

LoopForge bridges the gap between music and video:
1. **Audio in:** Loads audio file (WAV, MP3, FLAC, OGG).
2. **Analysis out:** Detects BPM, confidence, downbeats, and beat grids.
3. **Region selection:** User (or algorithm) selects a region near a target duration (e.g. 10.0 seconds).
4. **Prompt Spec generated:** Emits a pasteable prompt block with exact frame counts @ target FPS, residual drift (in ms), cadence recommendations for subject movement, and loop mode advisories (ping-pong vs true-cycle).

---

## ✨ Features

- **Lightweight Tempo Detection:** In-process spectral-flux onset envelope and autocorrelation detection (no heavy `librosa` dependency).
- **Sub-Harmonic & Octave Resolution:** Prior-weighted BPM selection with confidence scoring and quick `×2` / `÷2` octave toggle buttons.
- **Beat-Count Candidate Ranking:** Automatically enumerates integer beat counts within ±15% of target duration, ranking whole-bar multiples first.
- **Exact Frame & Residual Drift Math:** Calculates precise frame count `@24fps`, `@30fps`, or `@60fps` and reports signed residual drift (ms) without silent rounding.
- **Cadence Ladder:** Computes gesture counts and intervals for subdivisions (per beat, per 2 beats, per bar, per 2 bars), highlighting recommendations in the 0.9s–2.2s human movement window.
- **Loop Mode Advisories:** Provides guidance for `ping_pong` (guaranteed seam-free, doubles effective length) vs `true_cycle` (for directional motion like falling hair or smoke).
- **Interactive Dark-Mode GUI:** PySide6 desktop interface with custom waveform painter, beat/downbeat tick overlays, drag-selection with grid snapping (`detected` or `arithmetic`), and a 1-click **"Copy Spec Block"** clipboard button.
- **Headless CLI:** Fully scriptable CLI entry point for headless batch processing.
- **Portable Build:** PyInstaller script for single-file executable output (`dist/LoopForge.exe`).

---

## 🚀 Quickstart

### Prerequisites

- Python 3.11+
- ffmpeg on PATH (optional, for exotic audio formats)

### Installation

```bash
git clone https://github.com/horvathandras333-netizen/Music-analyser.git
cd Music-analyser
pip install -e .
```

---

## 💻 Usage

### 1. Graphical User Interface (GUI)

Launch the desktop interface:

```bash
python main.py
```

Or run the portable build executable:

```bash
python build_portable.py
# Executable generated in dist/LoopForge.exe
```

**GUI Workflow:**
1. Click **Open Audio File...** to load a track.
2. Drag across the waveform to select a region (snaps to beats/downbeats automatically).
3. Adjust **FPS**, **Target (s)**, **Loop Mode**, or **BPM (×2 / ÷2)** in the toolbar.
4. Click **Copy Spec Block** to copy the formatted prompt specification to your clipboard.

### 2. Headless CLI

Run track analysis directly from your terminal:

```bash
python cli.py analyze path/to/track.wav --target 10 --fps 24 --loop-mode ping_pong
```

#### CLI Output Example

```text
TRACK: Sunfire.wav
BPM: 145.02 (confidence 0.91) | Meter: 4/4 | First downbeat: 0.284s
SELECTED REGION: 32.114s - 42.045s (bars 20-26)

CLIP SPEC
Duration: 9.931s (24 beats / 6.0 bars)
Frames @24fps: 238 (residual drift +14ms, sub-frame)
Loop mode: ping-pong (effective 19.862s)

CADENCE
  per beat    0.414s   x24.0
  per 2 beats 0.828s   x12.0
  per bar     1.655s   x6.0    <- recommended
  per 2 bars  3.310s   x3.0

PROMPT FRAGMENT
Static locked-off camera, no drift or push. Subject completes one full
weight-shift every 1.66 seconds. Pose at 9.93s is identical to pose at
0.00s. Seamlessly loopable. 24fps.

ADVISORY
Ping-pong playback reverses motion. Safe for sways, turns, and breathing.
Not safe for hair fall, smoke, or particles - switch to true-cycle.
```

---

## 🛠️ Development & Testing

Run unit & integration tests:

```bash
pytest
```

Run linter:

```bash
ruff check .
```

---

## 📜 License

MIT License. Free for personal and commercial use.
