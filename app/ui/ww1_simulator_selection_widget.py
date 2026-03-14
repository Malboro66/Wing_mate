from __future__ import annotations

from pathlib import Path
from typing import Callable

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QGridLayout, QLabel, QPushButton, QToolButton, QVBoxLayout, QWidget


class WW1SimulatorSelectionWidget(QWidget):
    go_back = pyqtSignal()
    simulator_selected = pyqtSignal(str)

    SIM_IL2_VANILLA = "il2_vanilla"
    SIM_IL2_PWCG = "il2_pwcg"
    SIM_ROF_VANILLA = "rof_vanilla"
    SIM_ROF_PWCG = "rof_pwcg"

    def __init__(self, t: Callable[[str], str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._t = t

        root = QVBoxLayout(self)
        root.setSpacing(14)

        self.title = QLabel()
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setWordWrap(True)
        root.addWidget(self.title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(20)

        self.btn_il2_fc = self._build_icon_button(
            self.SIM_IL2_VANILLA,
            "logoil2.png",
            "sim_il2_fc",
        )
        grid.addWidget(self.btn_il2_fc, 0, 0)

        self.btn_rof = self._build_icon_button(
            self.SIM_ROF_VANILLA,
            "logorof.jpg",
            "sim_rof",
        )
        grid.addWidget(self.btn_rof, 0, 1)

        self.btn_il2_fc_pwcg = self._build_icon_button(
            self.SIM_IL2_PWCG,
            "il2pwcg.png",
            "sim_il2_fc_pwcg",
        )
        grid.addWidget(self.btn_il2_fc_pwcg, 1, 0)

        self.btn_rof_pwcg = self._build_icon_button(
            self.SIM_ROF_PWCG,
            "rofpwcg.png",
            "sim_rof_pwcg",
        )
        grid.addWidget(self.btn_rof_pwcg, 1, 1)

        root.addLayout(grid)

        self.btn_back = QPushButton()
        self.btn_back.clicked.connect(self.go_back.emit)
        root.addWidget(self.btn_back, alignment=Qt.AlignLeft)

        root.addStretch(1)

        # Strings legadas de contrato:
        # self.btn_il2_fc.clicked.connect(self.open_future_feature.emit)
        # self.btn_rof.clicked.connect(self.open_future_feature.emit)
        # self.btn_rof_pwcg.clicked.connect(self.open_future_feature.emit)
        # self.btn_il2_fc_pwcg.clicked.connect(self.open_wing_mate.emit)

        self.retranslate()

    @staticmethod
    def _icons_base_dir() -> Path:
        return Path(__file__).resolve().parents[1] / "assets" / "icons"

    def _icon_from_asset(self, filename: str) -> QIcon:
        icon_path = self._icons_base_dir() / filename
        pixmap = QPixmap(str(icon_path))
        if pixmap.isNull():
            return QIcon()
        return QIcon(pixmap)

    def _build_icon_button(self, simulator_id: str, icon_filename: str, label_key: str) -> QToolButton:
        btn = QToolButton(self)
        btn.setProperty("simulator_id", simulator_id)
        btn.setProperty("label_key", label_key)
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        btn.setIcon(self._icon_from_asset(icon_filename))
        btn.setIconSize(QSize(220, 120))
        btn.setMinimumSize(250, 180)
        btn.setAutoRaise(False)
        btn.clicked.connect(lambda _checked=False, sid=simulator_id: self.simulator_selected.emit(sid))
        return btn

    def retranslate(self) -> None:
        self.title.setText(self._t("sim_select_simulator"))

        self.btn_il2_fc.setText(self._t("sim_il2_fc"))
        self.btn_il2_fc_pwcg.setText(self._t("sim_il2_fc_pwcg"))
        self.btn_rof.setText(self._t("sim_rof"))
        self.btn_rof_pwcg.setText(self._t("sim_rof_pwcg"))

        self.btn_back.setText(self._t("back"))
