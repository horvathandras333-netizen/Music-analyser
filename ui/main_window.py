from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from analysis.decode import load_audio
from analysis.grid import analyze_track
from models import TrackAnalysis
from spec.builder import build_clip_spec
from spec.candidates import enumerate_candidates
from ui.spec_panel import SpecPanel
from ui.waveform import WaveformWidget


class MainWindow(QMainWindow):
    """LoopForge PySide6 main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LoopForge — Music Loop Spec Analyzer")
        self.resize(1100, 650)

        self.current_analysis: TrackAnalysis | None = None
        self.current_fps: int = 24
        self.current_loop_mode: str = "ping_pong"

        self._init_ui()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Top Control Bar
        control_bar = QHBoxLayout()
        self.btn_open = QPushButton("Open Audio File...")
        self.btn_open.clicked.connect(self._on_open_file)
        control_bar.addWidget(self.btn_open)

        # Grid Mode Toggle
        control_bar.addWidget(QLabel("Grid Mode:"))
        self.combo_grid_mode = QComboBox()
        self.combo_grid_mode.addItems(["Detected", "Arithmetic"])
        self.combo_grid_mode.currentTextChanged.connect(self._on_grid_mode_changed)
        control_bar.addWidget(self.combo_grid_mode)

        self.lbl_info = QLabel("No track loaded.")
        self.lbl_info.setStyleSheet("color: #cdd6f4; font-size: 13px;")
        control_bar.addWidget(self.lbl_info)
        control_bar.addStretch()

        main_layout.addLayout(control_bar)

        # Main Splitter View (Waveform Top / Spec Panel Bottom)
        splitter = QSplitter(Qt.Orientation.Vertical)

        self.waveform = WaveformWidget(self)
        self.waveform.selection_changed.connect(self._on_selection_changed)
        splitter.addWidget(self.waveform)

        self.spec_panel = SpecPanel(self)
        splitter.addWidget(self.spec_panel)

        splitter.setSizes([260, 340])
        main_layout.addWidget(splitter, stretch=1)

        # Dark palette styling
        self.setStyleSheet(
            """
            QMainWindow { background-color: #11111b; }
            QWidget { background-color: #11111b; color: #cdd6f4; }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                padding: 6px 14px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45475a; }
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                padding: 4px 8px;
                border-radius: 4px;
            }
            """
        )

    def _on_open_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Audio File", "", "Audio Files (*.wav *.mp3 *.flac *.ogg)"
        )
        if file_path:
            self.load_track(Path(file_path))

    def _on_grid_mode_changed(self, mode_text: str) -> None:
        grid_mode = mode_text.lower()
        self.waveform.grid_mode = grid_mode
        if (
            self.waveform.selection_start_s is not None
            and self.waveform.selection_end_s is not None
        ):
            snapped_start = self.waveform.snap_time_to_grid(self.waveform.selection_start_s)
            snapped_end = self.waveform.snap_time_to_grid(self.waveform.selection_end_s)
            self.waveform.set_selection(snapped_start, snapped_end)
            self._on_selection_changed(snapped_start, snapped_end)

    def _on_selection_changed(self, start_s: float, end_s: float) -> None:
        if self.current_analysis is None:
            return

        spec = build_clip_spec(
            start_s=start_s,
            end_s=end_s,
            bpm=self.current_analysis.bpm,
            fps=self.current_fps,
            meter=self.current_analysis.meter,
            loop_mode=self.current_loop_mode,  # type: ignore
        )
        self.spec_panel.update_spec(self.current_analysis, spec)

    def load_track(self, file_path: Path) -> None:
        """Load and analyze an audio file, updating GUI components."""
        analysis = analyze_track(file_path)
        audio, sr = load_audio(file_path)

        self.current_analysis = analysis
        self.waveform.set_track(
            audio=audio,
            sample_rate=sr,
            beat_times=analysis.beat_times,
            downbeat_times=analysis.downbeat_times,
            bpm=analysis.bpm,
        )

        info_text = (
            f"Track: <b>{analysis.path.name}</b> | BPM: <b>{analysis.bpm:.2f}</b> "
            f"(conf {analysis.bpm_confidence:.2f}) | Duration: <b>{analysis.duration_s:.2f}s</b>"
        )
        self.lbl_info.setText(info_text)

        # Select initial region (e.g. top 10s candidate from first downbeat)
        start_s = analysis.downbeat_times[0] if analysis.downbeat_times else 0.0
        candidates = enumerate_candidates(analysis.bpm, target_duration_s=10.0, meter=analysis.meter)
        top_duration = candidates[0][2] if candidates else 10.0
        end_s = start_s + top_duration

        self.waveform.set_selection(start_s, end_s)
        self._on_selection_changed(start_s, end_s)
