from __future__ import annotations

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class SkeletonWidget(QWidget):
    """Overlay simples de skeleton com animação por QTimer no MainThread."""

    def __init__(self, message: str = "Carregando...", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(20, 20, 20, 140);")

        self._title = QLabel(message, self)
        self._title.setStyleSheet("color: #f1f1f1; font-weight: 600; font-size: 14px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)
        layout.addWidget(self._title)

        self._bars: list[QFrame] = []
        for _ in range(6):
            bar = QFrame(self)
            bar.setFixedHeight(14)
            bar.setStyleSheet("background-color: #5a5a5a; border-radius: 6px;")
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
        color = "#8a8a8a" if self._pulse_on else "#5a5a5a"
        for bar in self._bars:
            bar.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
