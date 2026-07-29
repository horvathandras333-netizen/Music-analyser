from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
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

MAX_RECENT_FILES = 5


class MainWindow(QMainWindow):
    """LoopForge PySide6 main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LoopForge — Music Loop Spec Analyzer")
        self.resize(1150, 700)

        self.settings = QSettings("LoopForge", "LoopForgeApp")
        self.current_analysis: TrackAnalysis | None = None
        self.current_fps: int = 24
        self.current_target: float = 10.0
        self.current_loop_mode: str = "ping_pong"

        self._init_menu()
        self._init_ui()

    def _init_menu(self) -> None:
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

        open_action = file_menu.addAction("&Open Audio File...")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_file)

        self.recent_menu = QMenu("Recent Files", self)
        file_menu.addMenu(self.recent_menu)
        self._update_recent_files_menu()

        file_menu.addSeparator()
        exit_action = file_menu.addAction("E&xit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Top Control Bar
        control_bar = QHBoxLayout()

        self.btn_open = QPushButton("Open File...")
        self.btn_open.clicked.connect(self._on_open_file)
        control_bar.addWidget(self.btn_open)

        # Grid Mode Toggle
        control_bar.addWidget(QLabel("Grid:"))
        self.combo_grid_mode = QComboBox()
        self.combo_grid_mode.addItems(["Detected", "Arithmetic"])
        self.combo_grid_mode.currentTextChanged.connect(self._on_grid_mode_changed)
        control_bar.addWidget(self.combo_grid_mode)

        # FPS Selector
        control_bar.addWidget(QLabel("FPS:"))
        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["24", "25", "30", "60"])
        self.combo_fps.currentTextChanged.connect(self._on_fps_changed)
        control_bar.addWidget(self.combo_fps)

        # Target Duration SpinBox
        control_bar.addWidget(QLabel("Target (s):"))
        self.spin_target = QDoubleSpinBox()
        self.spin_target.setRange(2.0, 60.0)
        self.spin_target.setValue(10.0)
        self.spin_target.setSingleStep(0.5)
        self.spin_target.valueChanged.connect(self._on_target_changed)
        control_bar.addWidget(self.spin_target)

        # Loop Mode Selector
        control_bar.addWidget(QLabel("Loop Mode:"))
        self.combo_loop_mode = QComboBox()
        self.combo_loop_mode.addItems(["ping_pong", "true_cycle"])
        self.combo_loop_mode.currentTextChanged.connect(self._on_loop_mode_changed)
        control_bar.addWidget(self.combo_loop_mode)

        # BPM Octave Toggles
        control_bar.addWidget(QLabel("BPM:"))
        self.btn_bpm_halve = QPushButton("÷2")
        self.btn_bpm_halve.setToolTip("Halve BPM (octave down)")
        self.btn_bpm_halve.clicked.connect(self._on_bpm_halve)
        control_bar.addWidget(self.btn_bpm_halve)

        self.btn_bpm_double = QPushButton("×2")
        self.btn_bpm_double.setToolTip("Double BPM (octave up)")
        self.btn_bpm_double.clicked.connect(self._on_bpm_double)
        control_bar.addWidget(self.btn_bpm_double)

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
                padding: 4px 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45475a; }
            QComboBox, QDoubleSpinBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                padding: 4px 6px;
                border-radius: 4px;
            }
            QMenuBar { background-color: #181825; color: #cdd6f4; }
            QMenuBar::item:selected { background-color: #313244; }
            QMenu { background-color: #181825; color: #cdd6f4; border: 1px solid #313244; }
            QMenu::item:selected { background-color: #313244; }
            """
        )

    def _on_open_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Audio File", "", "Audio Files (*.wav *.mp3 *.flac *.ogg)"
        )
        if file_path:
            self.load_track(Path(file_path))

    def _update_recent_files_menu(self) -> None:
        self.recent_menu.clear()
        recent_files = self.settings.value("recent_files", [], type=list)
        if not recent_files:
            no_recent_action = self.recent_menu.addAction("No Recent Files")
            no_recent_action.setEnabled(False)
            return

        for path_str in recent_files:
            p = Path(path_str)
            action = self.recent_menu.addAction(p.name)
            action.triggered.connect(lambda _, path=p: self.load_track(path))

    def _add_recent_file(self, file_path: Path) -> None:
        path_str = str(file_path.resolve())
        recent_files = self.settings.value("recent_files", [], type=list)
        if path_str in recent_files:
            recent_files.remove(path_str)
        recent_files.insert(0, path_str)
        recent_files = recent_files[:MAX_RECENT_FILES]
        self.settings.setValue("recent_files", recent_files)
        self._update_recent_files_menu()

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

    def _on_fps_changed(self, fps_text: str) -> None:
        self.current_fps = int(fps_text)
        self._refresh_spec()

    def _on_target_changed(self, val: float) -> None:
        self.current_target = val
        if self.current_analysis:
            start_s = (
                self.waveform.selection_start_s
                if self.waveform.selection_start_s is not None
                else 0.0
            )
            candidates = enumerate_candidates(
                self.current_analysis.bpm, target_duration_s=self.current_target, meter=self.current_analysis.meter
            )
            top_dur = candidates[0][2] if candidates else self.current_target
            end_s = start_s + top_dur
            self.waveform.set_selection(start_s, end_s)
            self._on_selection_changed(start_s, end_s)

    def _on_loop_mode_changed(self, mode: str) -> None:
        self.current_loop_mode = mode
        self._refresh_spec()

    def _on_bpm_halve(self) -> None:
        if self.current_analysis:
            self.current_analysis.bpm = round(self.current_analysis.bpm / 2.0, 2)
            self.waveform.bpm = self.current_analysis.bpm
            self._update_info_label()
            self._refresh_spec()

    def _on_bpm_double(self) -> None:
        if self.current_analysis:
            self.current_analysis.bpm = round(self.current_analysis.bpm * 2.0, 2)
            self.waveform.bpm = self.current_analysis.bpm
            self._update_info_label()
            self._refresh_spec()

    def _update_info_label(self) -> None:
        if self.current_analysis:
            info_text = (
                f"Track: <b>{self.current_analysis.path.name}</b> | BPM: <b>{self.current_analysis.bpm:.2f}</b> "
                f"(conf {self.current_analysis.bpm_confidence:.2f}) | Duration: <b>{self.current_analysis.duration_s:.2f}s</b>"
            )
            self.lbl_info.setText(info_text)

    def _refresh_spec(self) -> None:
        if (
            self.current_analysis
            and self.waveform.selection_start_s is not None
            and self.waveform.selection_end_s is not None
        ):
            self._on_selection_changed(
                self.waveform.selection_start_s, self.waveform.selection_end_s
            )

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
            downbeat_times=self.current_analysis.downbeat_times,
        )
        self.spec_panel.update_spec(self.current_analysis, spec)

    def load_track(self, file_path: Path) -> None:
        """Load and analyze an audio file, updating GUI components."""
        analysis = analyze_track(file_path)
        audio, sr = load_audio(file_path)

        self.current_analysis = analysis
        self._add_recent_file(file_path)

        self.waveform.set_track(
            audio=audio,
            sample_rate=sr,
            beat_times=analysis.beat_times,
            downbeat_times=analysis.downbeat_times,
            bpm=analysis.bpm,
        )

        self._update_info_label()

        start_s = analysis.downbeat_times[0] if analysis.downbeat_times else 0.0
        candidates = enumerate_candidates(
            analysis.bpm, target_duration_s=self.current_target, meter=analysis.meter
        )
        top_duration = candidates[0][2] if candidates else self.current_target
        end_s = start_s + top_duration

        self.waveform.set_selection(start_s, end_s)
        self._on_selection_changed(start_s, end_s)
