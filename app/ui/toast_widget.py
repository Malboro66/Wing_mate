from __future__ import annotations

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QLabel, QWidget

from app.ui.design_system import DSFeedback


class ToastWidget(QLabel):
    """Toast não-bloqueante para feedback ao usuário."""

    _STYLES = DSFeedback.TOAST_LEVEL_STYLES

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMargin(10)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setStyleSheet("border-radius:8px; padding:8px;")

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self.hide()

    def show_toast(self, level: str, message: str, timeout_ms: int) -> None:
        base = self._STYLES.get(level, self._STYLES["info"])
        self.setStyleSheet(f"border-radius:8px; padding:8px; {base}")
        self.setText(message or "")

        parent = self.parentWidget()
        if parent is not None:
            max_width = max(280, int(parent.width() * 0.65))
            self.setMaximumWidth(max_width)
            self.adjustSize()
            x = max(8, (parent.width() - self.width()) // 2)
            y = max(8, parent.height() - self.height() - 14)
            self.move(x, y)

        self.raise_()
        self.show()
        self._timer.start(max(800, int(timeout_ms or 0)))
