import numpy as np
from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class WaveformWidget(QWidget):
    """Custom painted waveform widget displaying audio amplitude, beat grid, and region selection."""

    selection_changed = Signal(float, float)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.audio: np.ndarray | None = None
        self.sample_rate: int = 44100
        self.bpm: float = 120.0
        self.beat_times: list[float] = []
        self.downbeat_times: list[float] = []
        self.duration_s: float = 0.0

        self.selection_start_s: float | None = None
        self.selection_end_s: float | None = None
        self.grid_mode: str = "detected"
        self.is_dragging: bool = False

        self.setMinimumHeight(180)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_track(
        self,
        audio: np.ndarray,
        sample_rate: int,
        beat_times: list[float],
        downbeat_times: list[float],
        bpm: float = 120.0,
    ) -> None:
        """Set audio data and beat markers for painting."""
        self.audio = audio
        self.sample_rate = sample_rate
        self.bpm = bpm
        self.beat_times = beat_times
        self.downbeat_times = downbeat_times
        self.duration_s = len(audio) / sample_rate if sample_rate > 0 else 0.0

        self.selection_start_s = None
        self.selection_end_s = None
        self.update()

    def set_selection(self, start_s: float, end_s: float) -> None:
        """Programmatically update selection bounds."""
        self.selection_start_s = max(0.0, min(self.duration_s, start_s))
        self.selection_end_s = max(0.0, min(self.duration_s, end_s))
        self.update()

    def snap_time_to_grid(self, t: float) -> float:
        """Snap a given time in seconds to nearest beat/downbeat based on current grid_mode."""
        if self.duration_s <= 0:
            return 0.0

        t_clamped = max(0.0, min(self.duration_s, t))

        if self.grid_mode == "detected" and self.beat_times:
            closest = min(self.beat_times, key=lambda b: abs(b - t_clamped))
            return closest

        if self.grid_mode == "arithmetic" and self.downbeat_times:
            first_db = self.downbeat_times[0]
            beat_period = 60.0 / self.bpm if self.bpm > 0 else 0.5
            k = round((t_clamped - first_db) / beat_period)
            snapped = first_db + k * beat_period
            return round(max(0.0, min(self.duration_s, snapped)), 4)

        return round(t_clamped, 4)

    def time_to_x(self, t: float) -> float:
        """Map time in seconds to horizontal pixel coordinate."""
        if self.duration_s <= 0 or self.width() <= 0:
            return 0.0
        return (t / self.duration_s) * self.width()

    def x_to_time(self, x: float) -> float:
        """Map horizontal pixel coordinate to time in seconds."""
        if self.width() <= 0:
            return 0.0
        return (x / self.width()) * self.duration_s

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.duration_s > 0:
            raw_t = self.x_to_time(event.position().x())
            snapped_t = self.snap_time_to_grid(raw_t)
            self.selection_start_s = snapped_t
            self.selection_end_s = snapped_t
            self.is_dragging = True
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self.is_dragging and self.duration_s > 0:
            raw_t = self.x_to_time(event.position().x())
            snapped_t = self.snap_time_to_grid(raw_t)
            self.selection_end_s = snapped_t
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            if self.selection_start_s is not None and self.selection_end_s is not None:
                start_s = min(self.selection_start_s, self.selection_end_s)
                end_s = max(self.selection_start_s, self.selection_end_s)
                if start_s == end_s:
                    beat_period = 60.0 / self.bpm if self.bpm > 0 else 0.5
                    end_s = min(self.duration_s, start_s + beat_period * 4)
                self.selection_start_s = start_s
                self.selection_end_s = end_s
                self.update()
                self.selection_changed.emit(start_s, end_s)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background fill
        painter.fillRect(self.rect(), QColor("#1e1e2e"))

        w = self.width()
        h = self.height()
        mid_y = h / 2.0

        if self.audio is None or len(self.audio) == 0 or self.duration_s <= 0:
            painter.setPen(QColor("#a6adc8"))
            painter.setFont(QFont("sans-serif", 12))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Open an audio file to display waveform")
            return

        # Draw waveform
        samples_per_pixel = max(1, len(self.audio) // max(1, w))
        pen_waveform = QPen(QColor("#89b4fa"), 1)
        painter.setPen(pen_waveform)

        for x in range(w):
            start_idx = x * samples_per_pixel
            end_idx = min(len(self.audio), (x + 1) * samples_per_pixel)
            if start_idx < len(self.audio):
                chunk = self.audio[start_idx:end_idx]
                min_val = float(np.min(chunk))
                max_val = float(np.max(chunk))
                y_top = mid_y - (max_val * (h * 0.4))
                y_bot = mid_y - (min_val * (h * 0.4))
                painter.drawLine(x, int(y_top), x, int(y_bot))

        # Overlay beat ticks
        pen_beat = QPen(QColor("#585b70"), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen_beat)
        for t_beat in self.beat_times:
            x_pos = int(self.time_to_x(t_beat))
            if 0 <= x_pos <= w:
                painter.drawLine(x_pos, 0, x_pos, h)

        # Overlay downbeat ticks
        pen_downbeat = QPen(QColor("#f9e2af"), 2)
        painter.setPen(pen_downbeat)
        for t_down in self.downbeat_times:
            x_pos = int(self.time_to_x(t_down))
            if 0 <= x_pos <= w:
                painter.drawLine(x_pos, 0, x_pos, h)

        # Draw Selection Overlay
        if self.selection_start_s is not None and self.selection_end_s is not None:
            t1 = min(self.selection_start_s, self.selection_end_s)
            t2 = max(self.selection_start_s, self.selection_end_s)
            x1 = int(self.time_to_x(t1))
            x2 = int(self.time_to_x(t2))
            rect_w = max(1, x2 - x1)

            # Translucent selection region fill
            painter.fillRect(QRect(x1, 0, rect_w, h), QColor(137, 180, 250, 60))

            # Selection edge handles
            pen_handle = QPen(QColor("#cba6f7"), 2)
            painter.setPen(pen_handle)
            painter.drawLine(x1, 0, x1, h)
            painter.drawLine(x2, 0, x2, h)
