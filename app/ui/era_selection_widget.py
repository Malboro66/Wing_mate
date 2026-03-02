from __future__ import annotations

from typing import Callable

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.design_system import DSStyles
from utils.notification_bus import notify_info


class _GatedButton(QPushButton):
    attempted_when_disabled = pyqtSignal()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if not self.isEnabled():
            self.attempted_when_disabled.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class EraSelectionWidget(QWidget):
    ww1_selected = pyqtSignal()
    ww2_selected = pyqtSignal()

    def __init__(self, t: Callable[[str], str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._t = t

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        self.warning_label = QLabel(self._t("sim_setup_warning"))
        self.warning_label.setStyleSheet(DSStyles.STATE_WARNING)
        layout.addWidget(self.warning_label)

        self.btn_ww1 = _GatedButton(self._t("era_ww1"))
        self.btn_ww1.setMinimumHeight(56)
        self.btn_ww1.setEnabled(False)
        self.btn_ww1.clicked.connect(self.ww1_selected.emit)
        self.btn_ww1.attempted_when_disabled.connect(lambda: notify_info(self._t("sim_setup_warning")))
        layout.addWidget(self.btn_ww1)

        self.btn_ww2 = _GatedButton(self._t("era_ww2"))
        self.btn_ww2.setMinimumHeight(56)
        self.btn_ww2.setEnabled(False)
        self.btn_ww2.clicked.connect(self.ww2_selected.emit)
        self.btn_ww2.attempted_when_disabled.connect(lambda: notify_info(self._t("sim_setup_warning")))
        layout.addWidget(self.btn_ww2)

        layout.addStretch(1)

    def update_gate_status(self, ww1_ready: bool, ww2_ready: bool) -> None:
        self.btn_ww1.setEnabled(bool(ww1_ready))
        self.btn_ww2.setEnabled(bool(ww2_ready))
        self.warning_label.setVisible(not (ww1_ready or ww2_ready))

    def retranslate(self) -> None:
        self.warning_label.setText(self._t("sim_setup_warning"))
        self.btn_ww1.setText(self._t("era_ww1"))
        self.btn_ww2.setText(self._t("era_ww2"))
