from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTextEdit, QVBoxLayout, QWidget

from models import ClipSpec, TrackAnalysis
from report.render import render_report


class SpecPanel(QWidget):
    """Read-only spec display panel showing formatted report block with a Copy button."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Header bar with Copy button
        header_layout = QHBoxLayout()
        header_layout.addStretch()

        self.btn_copy = QPushButton("Copy Spec Block")
        self.btn_copy.setToolTip("Copy formatted spec block to clipboard")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        header_layout.addWidget(self.btn_copy)

        layout.addLayout(header_layout)

        # Report text view
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
        layout.addWidget(self.text_display, stretch=1)

    def copy_to_clipboard(self) -> None:
        """Copy current report text to system clipboard and provide visual feedback."""
        text = self.text_display.toPlainText()
        if text:
            clipboard = QGuiApplication.clipboard()
            if clipboard:
                clipboard.setText(text)
                self.btn_copy.setText("Copied!")
                QTimer.singleShot(2000, lambda: self.btn_copy.setText("Copy Spec Block"))

    def update_spec(self, analysis: TrackAnalysis, spec: ClipSpec) -> None:
        """Update spec display with rendered report text block."""
        report_text = render_report(analysis, spec)
        self.text_display.setPlainText(report_text)
