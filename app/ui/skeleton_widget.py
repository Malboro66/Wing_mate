from __future__ import annotations

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from app.ui.design_system_v3 import DSColors, DSStyles, DSFeedback, DSSpacing, DSStates, apply_primary_button, apply_ghost_button, apply_section_group, font_display, font_ui, font_body


class SkeletonWidget(QWidget):
    """Overlay simples de skeleton com animação por QTimer no MainThread."""

    def __init__(self, message: str = "Carregando...", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        from app.ui.design_system_v3 import font_ui, font_display, DSFeedback
        self._title = QLabel(message, self)
        self._title.setFont(font_ui(13, bold=True))
        self._title.setStyleSheet(DSFeedback.LOADING_TITLE_TEXT)
        self.setStyleSheet(f"QWidget {{ {DSFeedback.LOADING_OVERLAY_BG} }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)
        layout.addWidget(self._title)

        self._bars: list[QFrame] = []
        for _ in range(6):
            bar = QFrame(self)
            bar.setFixedHeight(14)
            bar.setStyleSheet(f"background-color: {DSFeedback.LOADING_BAR_IDLE}; border-radius: 6px;")
            layout.addWidget(bar)
            self._bars.append(bar)

        layout.addStretch(1)

        self._pulse_on = False
        self._timer = QTimer(self)
        self._timer.setInterval(260)
        self._timer.timeout.connect(self._tick)
        self.hide()

    def set_message(self, message: str) -> None:
        self._title.setText(message or "Carregando...")

    def showEvent(self, event) -> None:  # noqa: N802
        self._timer.start()
        super().showEvent(event)

    def hideEvent(self, event) -> None:  # noqa: N802
        self._timer.stop()
        super().hideEvent(event)

    def _tick(self) -> None:
        self._pulse_on = not self._pulse_on
        color = DSFeedback.LOADING_BAR_ACTIVE if self._pulse_on else DSFeedback.LOADING_BAR_IDLE
        for bar in self._bars:
            bar.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
