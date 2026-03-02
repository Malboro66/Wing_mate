from __future__ import annotations

from typing import Callable

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget

from app.ui.design_system import DSStyles


class FutureFeatureWidget(QWidget):
    go_back = pyqtSignal()

    def __init__(self, t: Callable[[str], str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._t = t

        root = QVBoxLayout(self)
        self.label = QLabel(self._t("future_feature_message"))
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(DSStyles.STATE_INFO)
        root.addStretch(1)
        root.addWidget(self.label)
        root.addStretch(1)

        footer = QHBoxLayout()
        self.btn_back = QPushButton(self._t("back"))
        self.btn_back.clicked.connect(self.go_back.emit)
        footer.addWidget(self.btn_back)
        footer.addStretch(1)
        root.addLayout(footer)

    def retranslate(self) -> None:
        self.label.setText(self._t("future_feature_message"))
        self.btn_back.setText(self._t("back"))
