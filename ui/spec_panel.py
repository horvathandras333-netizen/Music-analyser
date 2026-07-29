from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget

from models import ClipSpec, TrackAnalysis
from report.render import render_report


class SpecPanel(QWidget):
    """Read-only spec display panel showing formatted report block."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_display = QTextEdit(self)
        self.text_display.setReadOnly(True)
        self.text_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.text_display.setStyleSheet(
            """
            QTextEdit {
                background-color: #181825;
                color: #cdd6f4;
                font-family: Consolas, "Courier New", monospace;
                font-size: 13px;
                border: 1px solid #313244;
                border-radius: 4px;
                padding: 8px;
            }
            """
        )
        layout.addWidget(self.text_display)

    def update_spec(self, analysis: TrackAnalysis, spec: ClipSpec) -> None:
        """Update spec display with rendered report text block."""
        report_text = render_report(analysis, spec)
        self.text_display.setPlainText(report_text)
