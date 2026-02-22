from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QPoint, QSize, Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget


class MedalHoverPopup(QWidget):
    ZOOM_SIZE = QSize(320, 360)
    DELAY_MS = 600

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.ToolTip)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setStyleSheet(
            "background:#2a2a2a; border:1px solid #555;"
            "border-radius:6px;"
        )

        self._name_label = QLabel()
        self._name_label.setAlignment(Qt.AlignCenter)
        self._name_label.setStyleSheet("color:#d8d8d8; font-size:13px;")

        layout.addWidget(self._image_label)
        layout.addWidget(self._name_label)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.show)

    def schedule(self, pixmap: QPixmap, name: str, pos: QPoint) -> None:
        scaled = pixmap.scaled(self.ZOOM_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._image_label.setPixmap(scaled)
        self._name_label.setText(name)
        self.adjustSize()
        self.move(pos + QPoint(16, 16))
        self._timer.start(self.DELAY_MS)

    def cancel(self) -> None:
        self._timer.stop()
        self.hide()

