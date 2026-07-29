import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class WaveformWidget(QWidget):
    """Custom painted waveform widget displaying audio amplitude and beat grid overlays."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.audio: np.ndarray | None = None
        self.sample_rate: int = 44100
        self.beat_times: list[float] = []
        self.downbeat_times: list[float] = []
        self.duration_s: float = 0.0

        self.setMinimumHeight(180)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_track(
        self,
        audio: np.ndarray,
        sample_rate: int,
        beat_times: list[float],
        downbeat_times: list[float],
    ) -> None:
        """Set audio data and beat markers for painting."""
        self.audio = audio
        self.sample_rate = sample_rate
        self.beat_times = beat_times
        self.downbeat_times = downbeat_times
        self.duration_s = len(audio) / sample_rate if sample_rate > 0 else 0.0
        self.update()

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
