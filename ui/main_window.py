from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from analysis.decode import load_audio
from analysis.grid import analyze_track
from models import TrackAnalysis
from ui.waveform import WaveformWidget


class MainWindow(QMainWindow):
    """LoopForge PySide6 main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LoopForge — Music Loop Spec Analyzer")
        self.resize(1000, 600)

        self.current_analysis: TrackAnalysis | None = None
        self.current_audio: None = None

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

        self.lbl_info = QLabel("No track loaded.")
        self.lbl_info.setStyleSheet("color: #cdd6f4; font-size: 13px;")
        control_bar.addWidget(self.lbl_info)
        control_bar.addStretch()

        main_layout.addLayout(control_bar)

        # Waveform View
        self.waveform = WaveformWidget(self)
        main_layout.addWidget(self.waveform, stretch=1)

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
            """
        )

    def _on_open_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Audio File", "", "Audio Files (*.wav *.mp3 *.flac *.ogg)"
        )
        if file_path:
            self.load_track(Path(file_path))

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
        )

        info_text = (
            f"Track: <b>{analysis.path.name}</b> | BPM: <b>{analysis.bpm:.2f}</b> "
            f"(conf {analysis.bpm_confidence:.2f}) | Duration: <b>{analysis.duration_s:.2f}s</b>"
        )
        self.lbl_info.setText(info_text)
