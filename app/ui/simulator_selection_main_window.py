from __future__ import annotations

from typing import Any

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QMainWindow, QPushButton, QStackedWidget, QStyle, QToolBar, QWidget, QSizePolicy

from app.application.app_config import AppConfig
from app.ui.era_selection_widget import EraSelectionWidget
from app.ui.future_feature_widget import FutureFeatureWidget
from app.ui.i18n import AppI18n
from app.ui.main_window import MainWindow as WingMateMainWindow
from app.ui.settings_widget import SettingsWidget
from app.ui.toast_widget import ToastWidget
from app.ui.ww1_simulator_selection_widget import WW1SimulatorSelectionWidget
from utils.notification_bus import notification_bus


class MainWindow(QMainWindow):
    """Janela raiz com QStackedWidget para fluxo de seleção de simulador/era."""

    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings("IL2CampaignAnalyzer", "Settings")
        self.config = AppConfig(self.settings)
        self._language_code = str(self.settings.value("ui/language", AppI18n.PT_BR) or AppI18n.PT_BR)

        self._history: list[int] = []

        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        self.era_widget = EraSelectionWidget(self._t)
        self.ww1_widget = WW1SimulatorSelectionWidget(self._t)
        self.future_widget = FutureFeatureWidget(self._t)
        self.settings_widget = SettingsWidget(self._t, self.config)
        self.wing_mate_widget = WingMateMainWindow()

        self._idx_era = self.stack.addWidget(self.era_widget)
        self._idx_ww1 = self.stack.addWidget(self.ww1_widget)
        self._idx_future = self.stack.addWidget(self.future_widget)
        self._idx_settings = self.stack.addWidget(self.settings_widget)
        self._idx_wing_mate = self.stack.addWidget(self.wing_mate_widget)

        self._build_toolbar()
        self._toast = ToastWidget(self)
        notification_bus.notified.connect(self._on_notification, Qt.QueuedConnection)

        self._wire_events()
        self._apply_language()
        self.refresh_gates()
        self._go_to(self._idx_era)

    def _t(self, key: str, **kwargs: Any) -> str:
        return AppI18n.t(key, self._language_code, **kwargs)

    def _build_toolbar(self) -> None:
        tb = QToolBar(self._t("toolbar_actions"), self)
        tb.setMovable(False)
        self.addToolBar(tb)

        spacer = QWidget(tb)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        self.btn_settings = QPushButton()
        self.btn_settings.setObjectName("settings_global_button")
        self.btn_settings.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.btn_settings.setToolTip(self._t("open_settings"))
        self.btn_settings.clicked.connect(lambda: self._go_to(self._idx_settings))
        tb.addWidget(self.btn_settings)

    def _wire_events(self) -> None:
        self.era_widget.ww1_selected.connect(lambda: self._go_to(self._idx_ww1))
        self.era_widget.ww2_selected.connect(lambda: self._go_to(self._idx_future))

        self.ww1_widget.go_back.connect(self._go_back)
        self.ww1_widget.open_future_feature.connect(lambda: self._go_to(self._idx_future))
        self.ww1_widget.open_wing_mate.connect(lambda: self._go_to(self._idx_wing_mate))

        self.future_widget.go_back.connect(self._go_back)
        self.settings_widget.go_back.connect(self._go_back)
        self.settings_widget.settings_changed.connect(self.refresh_gates)

    def _go_to(self, idx: int) -> None:
        cur = self.stack.currentIndex()
        if cur >= 0 and cur != idx:
            self._history.append(cur)
        self.stack.setCurrentIndex(idx)

    def _go_back(self) -> None:
        if self._history:
            self.stack.setCurrentIndex(self._history.pop())
        else:
            self.stack.setCurrentIndex(self._idx_era)

    def refresh_gates(self) -> None:
        self.era_widget.update_gate_status(self.config.ww1_ready(), self.config.ww2_ready())

    def _apply_language(self) -> None:
        self.setWindowTitle(self._t("sim_root_title"))
        self.btn_settings.setToolTip(self._t("open_settings"))

        self.era_widget.retranslate()
        self.ww1_widget.retranslate()
        self.future_widget.retranslate()
        self.settings_widget.retranslate()

    def _on_notification(self, level: str, message: str, timeout_ms: int) -> None:
        self._toast.show_toast(level, message, timeout_ms)
        self.statusBar().showMessage(message, max(1000, timeout_ms))
