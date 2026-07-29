import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.waveform import WaveformWidget


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_waveform_widget_coordinate_mapping(qapp):
    widget = WaveformWidget()
    audio = np.zeros(44100 * 10, dtype=np.float32)
    widget.set_track(audio, 44100, [0.5, 1.0], [0.5])
    widget.resize(1000, 200)

    assert widget.duration_s == 10.0
    assert widget.time_to_x(0.0) == 0.0
    assert widget.time_to_x(5.0) == 500.0
    assert widget.time_to_x(10.0) == 1000.0

    assert widget.x_to_time(0.0) == 0.0
    assert widget.x_to_time(500.0) == 5.0
    assert widget.x_to_time(1000.0) == 10.0


def test_main_window_instantiation(qapp):
    window = MainWindow()
    assert window.windowTitle().startswith("LoopForge")
    assert window.current_analysis is None
