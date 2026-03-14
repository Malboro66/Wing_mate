from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QMainWindow, QPushButton, QSizePolicy, QStackedWidget, QStyle, QToolBar, QWidget

from app.application.app_config import AppConfig
from app.ui.era_selection_widget import EraSelectionWidget
from app.ui.future_feature_widget import FutureFeatureWidget
from app.ui.i18n import AppI18n
from app.ui.main_window import MainWindow as WingMateMainWindow
from app.ui.settings_widget import SettingsWidget
from app.ui.toast_widget import ToastWidget
from app.ui.ww1_simulator_selection_widget import WW1SimulatorSelectionWidget
from utils.notification_bus import notification_bus, notify_info


class MainWindow(QMainWindow):
    """Root window using QStackedWidget for simulator and era navigation."""

    _IL2_VANILLA_STEAM_LIBRARY_REL = Path(
        "SteamLibrary/steamapps/common/IL-2 Sturmovik Battle of Stalingrad/data/Career"
    )
    _IL2_VANILLA_DEFAULT_STEAM_REL = Path(
        "Program Files (x86)/Steam/steamapps/common/IL-2 Sturmovik Battle of Stalingrad/data/Career"
    )

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
        self._go_to(self._idx_ww1)

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
        self.ww1_widget.simulator_selected.connect(self._on_simulator_selected)
        self.wing_mate_widget.go_back_requested.connect(self._go_back)

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
            self.stack.setCurrentIndex(self._idx_ww1)

    def _on_simulator_selected(self, simulator_id: str) -> None:
        self.wing_mate_widget.set_data_source_mode(self._resolve_data_source_mode(simulator_id))
        suggested_path = self._resolve_campaign_path_for_simulator(simulator_id)
        if suggested_path:
            self.wing_mate_widget.set_campaign_path(suggested_path, show_cp_db_notice=True)
        else:
            notify_info(self._t("sim_select_set_path_hint"))
        self._go_to(self._idx_wing_mate)

    @staticmethod
    def _resolve_data_source_mode(simulator_id: str) -> str:
        if simulator_id == WW1SimulatorSelectionWidget.SIM_IL2_VANILLA:
            return WingMateMainWindow.SOURCE_IL2_VANILLA
        if simulator_id in {
            WW1SimulatorSelectionWidget.SIM_IL2_PWCG,
            WW1SimulatorSelectionWidget.SIM_ROF_PWCG,
            WW1SimulatorSelectionWidget.SIM_ROF_VANILLA,
        }:
            return WingMateMainWindow.SOURCE_PWCG_JSON
        return WingMateMainWindow.SOURCE_AUTO

    def _resolve_campaign_path_for_simulator(self, simulator_id: str) -> Optional[str]:
        if simulator_id == WW1SimulatorSelectionWidget.SIM_IL2_VANILLA:
            return self._resolve_il2_vanilla_campaign_path()

        if simulator_id == WW1SimulatorSelectionWidget.SIM_IL2_PWCG:
            return self._resolve_pwcg_campaign_path(self.config.get_path(AppConfig.KEY_PWCG))

        if simulator_id == WW1SimulatorSelectionWidget.SIM_ROF_VANILLA:
            return self._resolve_pwcg_campaign_path(self.config.get_path(AppConfig.KEY_ROF))

        if simulator_id == WW1SimulatorSelectionWidget.SIM_ROF_PWCG:
            return self._resolve_pwcg_campaign_path(self.config.get_path(AppConfig.KEY_PWCG))

        return None

    @staticmethod
    def _resolve_pwcg_campaign_path(raw_path: str) -> Optional[str]:
        normalized = MainWindow._resolve_existing_directory(raw_path)
        if not normalized:
            return None

        path_obj = Path(normalized)
        if (path_obj / "User" / "Campaigns").is_dir():
            return str(path_obj)

        if path_obj.name.lower() == "campaigns" and path_obj.parent.name.lower() == "user":
            return str(path_obj)

        if path_obj.name.lower() == "user" and (path_obj / "Campaigns").is_dir():
            return str(path_obj / "Campaigns")

        if (path_obj / "Campaign.json").is_file():
            return str(path_obj.parent)

        return str(path_obj)

    def _resolve_il2_vanilla_campaign_path(self) -> Optional[str]:
        configured_fc = self._resolve_existing_directory(self.config.get_path(AppConfig.KEY_IL2_FC))
        if configured_fc:
            configured_fc_path = Path(configured_fc)
            if (configured_fc_path / "cp.db").is_file():
                return str(configured_fc_path)

            career_candidate = configured_fc_path / "data" / "Career"
            if career_candidate.is_dir():
                return str(career_candidate)

        for drive_root in self._candidate_drive_roots():
            for rel_path in (
                self._IL2_VANILLA_STEAM_LIBRARY_REL,
                self._IL2_VANILLA_DEFAULT_STEAM_REL,
            ):
                candidate = drive_root / rel_path
                if candidate.is_dir():
                    return str(candidate)

        return None

    @staticmethod
    def _resolve_existing_directory(raw_path: str) -> Optional[str]:
        normalized = str(raw_path or "").strip()
        if not normalized:
            return None

        path_obj = Path(normalized)
        if path_obj.exists() and path_obj.is_dir():
            return str(path_obj)
        return None

    @staticmethod
    def _candidate_drive_roots() -> list[Path]:
        drive_letters = [Path.home().drive]
        drive_letters.extend([f"{chr(code)}:" for code in range(ord("A"), ord("Z") + 1)])

        roots: list[Path] = []
        seen: set[str] = set()
        for drive in drive_letters:
            normalized = str(drive or "").strip().upper()
            if not normalized:
                continue
            if not normalized.endswith("\\"):
                normalized = f"{normalized}\\"
            if normalized in seen:
                continue
            seen.add(normalized)
            roots.append(Path(normalized))
        return roots

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
