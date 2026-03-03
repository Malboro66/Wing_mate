from __future__ import annotations

from typing import Callable

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout, QWidget


class WW1SimulatorSelectionWidget(QWidget):
    go_back = pyqtSignal()
    open_future_feature = pyqtSignal()
    open_wing_mate = pyqtSignal()

    def __init__(self, t: Callable[[str], str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._t = t

        root = QVBoxLayout(self)
        root.setSpacing(10)

        self.btn_il2_fc = QPushButton(self._t("sim_il2_fc"))
        self.btn_il2_fc.clicked.connect(self.open_future_feature.emit)
        root.addWidget(self.btn_il2_fc)

        self.btn_il2_fc_pwcg = QPushButton(self._t("sim_il2_fc_pwcg"))
        self.btn_il2_fc_pwcg.clicked.connect(self.open_wing_mate.emit)
        root.addWidget(self.btn_il2_fc_pwcg)

        self.btn_rof = QPushButton(self._t("sim_rof"))
        self.btn_rof.clicked.connect(self.open_future_feature.emit)
        root.addWidget(self.btn_rof)

        self.btn_rof_pwcg = QPushButton(self._t("sim_rof_pwcg"))
        self.btn_rof_pwcg.clicked.connect(self.open_future_feature.emit)
        root.addWidget(self.btn_rof_pwcg)

        root.addStretch(1)

        footer = QHBoxLayout()
        self.btn_back = QPushButton(self._t("back"))
        self.btn_back.clicked.connect(self.go_back.emit)
        footer.addWidget(self.btn_back)
        footer.addStretch(1)
        root.addLayout(footer)

    def retranslate(self) -> None:
        self.btn_il2_fc.setText(self._t("sim_il2_fc"))
        self.btn_il2_fc_pwcg.setText(self._t("sim_il2_fc_pwcg"))
        self.btn_rof.setText(self._t("sim_rof"))
        self.btn_rof_pwcg.setText(self._t("sim_rof_pwcg"))
        self.btn_back.setText(self._t("back"))
