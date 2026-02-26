# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - app/ui/main_window.py
# Janela principal com gerenciamento de abas e sincronização thread-safe
#
# Melhorias de UI:
# - QToolBar com atalhos (Ctrl+O, F5) e ação de copiar caminho
# - Progress bar embutido na StatusBar
# - Estado "busy" durante sincronização (desabilita ações/combos)
# - Label de caminho com elipse e atualização no resize
# - Persistência da última campanha selecionada (QSettings)
# ===================================================================

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, List, Any, Callable
from datetime import datetime
import json
import logging
import time

from PyQt5.QtCore import QSettings, QThread, pyqtSignal, QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap, QCloseEvent, QFontMetrics
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QFileDialog,
    QProgressBar,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QAction,
    QStyle,
    QApplication,
)

from app.ui.aces_tab import AcesTab
from app.ui.missions_tab import MissionsTab
from app.ui.squadron_tab import SquadronTab
from app.ui.profile_tab import ProfileTab
from app.ui.medals_tab import MedalsTab
from app.ui.insert_squads_tab import InsertSquadsTab
from app.ui.input_medals_tab import InputMedalsTab
from app.ui.skeleton_widget import SkeletonWidget
from app.ui.toast_widget import ToastWidget

from app.application.container import AppContainer
from app.application.mission_validation_service import Mission, MissionValidationService
from app.application.personnel_resolution_service import PersonnelResolutionService
from app.core.data_parser import IL2DataParser
from app.core.data_processor import IL2DataProcessor
from utils.notification_bus import notification_bus, notify_error, notify_warning
from utils.observability import Events, emit_event, record_action_duration, record_cache_stats
from utils.structured_logger import StructuredLogger

logger = logging.getLogger("IL2CampaignAnalyzer")
structured_logger = StructuredLogger("IL2CampaignAnalyzer")


class DataSyncThread(QThread):
    """
    Thread para sincronização de dados de campanhas PWCG de forma assíncrona.

    Signals:
        data_loaded: Emitido quando dados são carregados com sucesso (dict)
        error_occurred: Emitido quando ocorre erro (str)
        progress: Emitido para atualizar progresso (int 0-100)
    """

    data_loaded = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(
        self,
        pwcgfc_path: str,
        campaign_name: str,
        processor_factory: Optional[Callable[[str], IL2DataProcessor]] = None,
        parent: Optional[QThread] = None,
    ) -> None:
        super().__init__(parent)
        self.pwcgfc_path: str = pwcgfc_path
        self.campaign_name: str = campaign_name
        self.processor_factory = processor_factory or (lambda p: IL2DataProcessor(p))

    def run(self) -> None:
        sync_t0 = time.perf_counter()
        try:
            self.progress.emit(10)
            logger.info(
                "Iniciando sincronização: campanha=%s, path=%s",
                self.campaign_name,
                self.pwcgfc_path,
            )
            emit_event(
                structured_logger,
                Events.SYNC_STARTED,
                campaign_name=self.campaign_name,
                pwcgfc_path=self.pwcgfc_path,
            )

            processor = self.processor_factory(self.pwcgfc_path)
            self.progress.emit(40)

            data = processor.process_campaign(self.campaign_name)
            self.progress.emit(90)

            if not isinstance(data, dict) or not data:
                msg = "Não foi possível carregar os dados da campanha."
                logger.warning("Dados de campanha inválidos: %s", type(data))
                record_action_duration(
                    structured_logger,
                    "sync_campaign",
                    (time.perf_counter() - sync_t0) * 1000.0,
                    success=False,
                )
                self.error_occurred.emit(msg)
                self.progress.emit(0)
                return

            logger.info(
                "Sincronização concluída: %s missões, %s ases",
                len(data.get("missions", []) or []),
                len(data.get("aces", []) or []),
            )
            emit_event(
                structured_logger,
                Events.SYNC_SUCCEEDED,
                campaign_name=self.campaign_name,
                missions_count=len(data.get("missions", []) or []),
                aces_count=len(data.get("aces", []) or []),
            )
            record_action_duration(
                structured_logger,
                "sync_campaign",
                (time.perf_counter() - sync_t0) * 1000.0,
                success=True,
            )

            self.data_loaded.emit(data)
            self.progress.emit(100)

        except (OSError, json.JSONDecodeError, ValueError) as e:
            logger.exception("Erro na sincronização (dados/parse/arquivo)")
            emit_event(
                structured_logger,
                Events.SYNC_FAILED,
                level="error",
                campaign_name=self.campaign_name,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            record_action_duration(
                structured_logger,
                "sync_campaign",
                (time.perf_counter() - sync_t0) * 1000.0,
                success=False,
            )
            self.error_occurred.emit(f"Erro ao processar dados: {e}")
            self.progress.emit(0)

        except Exception as e:
            logger.exception("Erro inesperado na sincronização")
            emit_event(
                structured_logger,
                Events.SYNC_FAILED,
                level="error",
                campaign_name=self.campaign_name,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            record_action_duration(
                structured_logger,
                "sync_campaign",
                (time.perf_counter() - sync_t0) * 1000.0,
                success=False,
            )
            self.error_occurred.emit(f"Erro inesperado: {e}")
            try:
                self.progress.emit(0)
            except RuntimeError:
                logger.debug("Thread finalizada durante emissão de sinal de erro")


class MainWindow(QMainWindow):
    """
    Janela principal da aplicação Wing Mate.

    Responsabilidades:
    - Seleção de pasta PWCGFC e campanhas
    - Sincronização de dados em background via QThread
    - Gerenciamento de abas
    - Persistência via QSettings
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.settings: QSettings = QSettings("IL2CampaignAnalyzer", "Settings")
        self.container: AppContainer = AppContainer()
        self.personnel_resolution_service = PersonnelResolutionService(self.container.get_parser)
        self.mission_validation_service = MissionValidationService()

        self.pwcgfc_path: str = ""
        self._full_path_text: str = ""
        self.current_data: Dict[str, Any] = {}
        self._validated_missions: List[Mission] = []
        self.selected_mission_index: int = -1
        self.sync_thread: Optional[DataSyncThread] = None
        self._medals_loaded_once: bool = False
        self._medals_dirty: bool = True
        self._busy: bool = False

        # Widgets/actions referenciados em mais de um ponto
        self.path_label: QLabel
        self.campaign_combo: QComboBox
        self.tabs: QTabWidget

        self.action_open_folder: QAction
        self.action_sync: QAction
        self.action_copy_path: QAction
        self.btn_copy_path: QPushButton

        self.progress_bar: QProgressBar

        self.profile_tab: ProfileTab
        self.missions_tab: MissionsTab
        self.squadron_tab: SquadronTab
        self.aces_tab: AcesTab
        self.medals_tab: MedalsTab
        self.insert_squads_tab: InsertSquadsTab
        self.input_medals_tab: InputMedalsTab
        self._sync_skeletons: Dict[QWidget, SkeletonWidget] = {}

        self._build_ui()
        notification_bus.notified.connect(self._on_notification, Qt.QueuedConnection)
        self._load_saved_settings()

        try:
            modules = self.container.get_content_module_registry().list_modules()
            logger.info("Registro de conteúdo carregado: %s módulos", len(modules))
        except Exception:
            logger.exception("Falha ao carregar registro de módulos de conteúdo")

        logger.info("MainWindow inicializada")

    # ---------------- Paths/Assets ----------------

    @staticmethod
    def _icons_base_dir() -> Path:
        return Path(__file__).resolve().parents[1] / "assets" / "icons"

    def _icon_from_asset(self, filename: str, fallback_style_icon: QStyle.StandardPixmap) -> QIcon:
        p = self._icons_base_dir() / filename
        pm = QPixmap(str(p))
        if not pm.isNull():
            return QIcon(pm)
        return self.style().standardIcon(fallback_style_icon)

    def _set_app_icon(self) -> None:
        icon_path: Path = self._icons_base_dir() / "app_icon.png"
        pm: QPixmap = QPixmap(str(icon_path))
        if not pm.isNull():
            self.setWindowIcon(QIcon(pm))
        else:
            logger.warning("Ícone da aplicação não encontrado")

    # ---------------- UI helpers ----------------

    def _set_ui_busy(self, busy: bool, message: str = "") -> None:
        self._busy = bool(busy)

        self.action_sync.setEnabled(not self._busy)
        self.action_open_folder.setEnabled(True)  # permitir trocar pasta mesmo ocupado, se desejar
        self.campaign_combo.setEnabled(not self._busy)

        # Mantém as abas habilitadas; o feedback visual de loading vem dos skeletons.
        self.tabs.setEnabled(True)
        self._set_sync_skeletons_visible(self._busy, message or "Sincronizando campanha...")

        self.progress_bar.setVisible(self._busy)
        if message:
            self.statusBar().showMessage(message, 0)

    def _update_elided_path_label(self) -> None:
        txt = self._full_path_text or "Nenhum caminho selecionado"
        # Elide para caber, deixando o restante do layout respirar
        fm = QFontMetrics(self.path_label.font())
        maxw = max(200, self.path_label.width())
        elided = fm.elidedText(txt, Qt.ElideMiddle, maxw)
        self.path_label.setText(elided)
        self.path_label.setToolTip(self._full_path_text or "")

        self.action_copy_path.setEnabled(bool(self._full_path_text))

    # ---------------- Construção da UI ----------------

    def _build_ui(self) -> None:
        self.setWindowTitle("Wing Mate")
        self._set_app_icon()
        self.setGeometry(100, 100, 1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Toolbar
        tb = QToolBar("Ações", self)
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))
        self.addToolBar(tb)

        self.action_open_folder = QAction(
            self._icon_from_asset("config.png", QStyle.SP_DirOpenIcon),
            "Selecionar Pasta PWCGFC",
            self,
        )
        self.action_open_folder.setShortcut("Ctrl+O")
        self.action_open_folder.triggered.connect(self._select_pwcgfc_folder)

        self.action_sync = QAction(
            self._icon_from_asset("sync.png", QStyle.SP_BrowserReload),
            "Sincronizar Dados",
            self,
        )
        self.action_sync.setShortcut("F5")
        self.action_sync.triggered.connect(self._sync_data)

        self.action_copy_path = QAction(
            self.style().standardIcon(QStyle.SP_DialogSaveButton),
            "Copiar caminho",
            self,
        )
        self.action_copy_path.setShortcut("Ctrl+C")
        self.action_copy_path.triggered.connect(self._copy_current_path_to_clipboard)
        self.action_copy_path.setEnabled(False)

        tb.addAction(self.action_open_folder)
        tb.addAction(self.action_sync)
        tb.addSeparator()
        tb.addAction(self.action_copy_path)

        # Linha do caminho (compacta)
        path_row = QHBoxLayout()
        self.path_label = QLabel("Nenhum caminho selecionado")
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        path_row.addWidget(self.path_label, 1)

        # Botão pequeno de copiar (espelha a ação)
        self.btn_copy_path = QPushButton("Copiar")
        self.btn_copy_path.setToolTip("Copiar caminho do PWCGFC")
        self.btn_copy_path.setAccessibleName("copiar_caminho_button")
        self.btn_copy_path.clicked.connect(self._copy_current_path_to_clipboard)
        self.btn_copy_path.setFixedHeight(28)
        path_row.addWidget(self.btn_copy_path, 0)

        layout.addLayout(path_row)

        # Seletor de campanha
        row = QHBoxLayout()
        row.addWidget(QLabel("Campanha:"))
        self.campaign_combo = QComboBox()
        self.campaign_combo.setAccessibleName("campaign_selector")
        self.campaign_combo.currentTextChanged.connect(self._on_campaign_changed)
        row.addWidget(self.campaign_combo, 1)
        layout.addLayout(row)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setAccessibleName("main_tabs")
        self.tabs.currentChanged.connect(self._on_tab_changed)

        self.profile_tab = ProfileTab(settings=self.settings)
        self.tabs.addTab(self.profile_tab, "Perfil do Piloto")

        self.missions_tab = MissionsTab()
        self.missions_tab.missionSelected.connect(self._on_mission_selected)
        self.tabs.addTab(self.missions_tab, "Missões")

        self.squadron_tab = SquadronTab()
        self.tabs.addTab(self.squadron_tab, "Esquadrão")

        self.aces_tab = AcesTab()
        self.tabs.addTab(self.aces_tab, "Ases")

        self.medals_tab = MedalsTab()
        self.tabs.addTab(self.medals_tab, "Medalhas")

        self.insert_squads_tab = InsertSquadsTab(
            app_service=self.container.get_squadron_enrichment_application_service()
        )
        self.tabs.addTab(self.insert_squads_tab, "Insert Squads")

        self.input_medals_tab = InputMedalsTab()
        self.tabs.addTab(self.input_medals_tab, "Input Medals")

        # Sinais: recarrega medalhas quando cadastrar/editar
        try:
            self.input_medals_tab.medal_added.connect(lambda _: self._mark_medals_dirty())
            self.input_medals_tab.medal_updated.connect(lambda _i, _m: self._mark_medals_dirty())
        except AttributeError:
            logger.warning(
                "Não foi possível conectar sinais da aba Input Medals. "
                "A aba pode não ter sido inicializada corretamente."
            )

        layout.addWidget(self.tabs)

        # StatusBar + progress embutido
        sb = QStatusBar()
        self.setStatusBar(sb)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(180)
        self.progress_bar.setTextVisible(True)
        sb.addPermanentWidget(self.progress_bar)

        self._toast = ToastWidget(self)
        self._build_sync_skeletons()

        # Ordem mínima de foco para navegação por teclado
        self.setTabOrder(self.campaign_combo, self.btn_copy_path)
        self.setTabOrder(self.btn_copy_path, self.tabs)
        self.tabs.setFocusPolicy(Qt.StrongFocus)

        self._set_ui_busy(False)


    def _build_sync_skeletons(self) -> None:
        sync_tabs: List[QWidget] = [
            self.profile_tab,
            self.missions_tab,
            self.squadron_tab,
            self.aces_tab,
            self.medals_tab,
        ]
        for tab in sync_tabs:
            overlay = SkeletonWidget(parent=tab)
            overlay.setGeometry(tab.rect())
            overlay.hide()
            self._sync_skeletons[tab] = overlay

    def _refresh_sync_skeleton_geometry(self) -> None:
        for tab, overlay in self._sync_skeletons.items():
            overlay.setGeometry(tab.rect())

    def _set_sync_skeletons_visible(self, visible: bool, message: str) -> None:
        self._refresh_sync_skeleton_geometry()
        for overlay in self._sync_skeletons.values():
            overlay.set_message(message)
            overlay.setVisible(visible)
            if visible:
                overlay.raise_()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_elided_path_label()
        self._refresh_sync_skeleton_geometry()

    def _on_notification(self, level: str, message: str, timeout_ms: int) -> None:
        self._toast.show_toast(level, message, timeout_ms)
        self.statusBar().showMessage(message, max(1000, timeout_ms))

    # ---------------- Fechamento ----------------

    def closeEvent(self, event: QCloseEvent) -> None:
        try:
            if self.sync_thread and self.sync_thread.isRunning():
                logger.info("Aguardando finalização de thread de sincronização...")
                self.sync_thread.quit()
                self.sync_thread.wait(3000)
        except (RuntimeError, AttributeError):
            logger.debug("Erro ao tentar finalizar thread de sincronização durante fechamento")

        logger.info("Aplicação encerrada")
        super().closeEvent(event)

    # ---------------- Ações ----------------

    def _copy_current_path_to_clipboard(self) -> None:
        if not self._full_path_text:
            self.statusBar().showMessage("Nenhum caminho para copiar.", 2500)
            return
        QApplication.clipboard().setText(self._full_path_text)
        self.statusBar().showMessage("Caminho copiado para a área de transferência.", 2500)

    def _select_pwcgfc_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta PWCGFC")
        if not folder_path:
            return

        self.pwcgfc_path = folder_path
        self.container.set_pwcgfc_path(self.pwcgfc_path)
        self._full_path_text = f"Caminho: {folder_path}"
        self.settings.setValue("pwcgfc_path", self.pwcgfc_path)
        self._update_elided_path_label()

        logger.info("Pasta PWCGFC selecionada: %s", folder_path)

        self._load_campaigns()

        # Propaga caminho para abas que necessitam
        try:
            self.insert_squads_tab.set_pwcgfc_path(self.pwcgfc_path)
        except AttributeError:
            pass
        try:
            self.input_medals_tab.set_pwcgfc_path(self.pwcgfc_path)
        except AttributeError:
            pass

    def _load_campaigns(self) -> None:
        if not self.pwcgfc_path:
            return

        parser = self.container.get_parser()
        campaigns: List[str] = parser.get_campaigns()

        self.campaign_combo.blockSignals(True)
        self.campaign_combo.clear()
        self.campaign_combo.addItems(campaigns)
        self.campaign_combo.blockSignals(False)

        saved_campaign = str(self.settings.value("ui/last_campaign", "") or "")
        if saved_campaign and saved_campaign in campaigns:
            self.campaign_combo.setCurrentText(saved_campaign)

        self.statusBar().showMessage(f"{len(campaigns)} campanhas carregadas.", 3000)
        logger.info("Carregadas %s campanhas", len(campaigns))

    def _on_campaign_changed(self, campaign: str) -> None:
        c = (campaign or "").strip()
        if c:
            self.settings.setValue("ui/last_campaign", c)

    # ---------------- Sync ----------------

    def _sync_data(self) -> None:
        campaign: str = self.campaign_combo.currentText().strip()
        if not self.pwcgfc_path or not campaign:
            notify_warning("Selecione a pasta PWCGFC e uma campanha.")
            return

        if self.sync_thread and self.sync_thread.isRunning():
            self.statusBar().showMessage("Sincronização já em andamento...", 2500)
            return

        self._set_ui_busy(True, "Sincronizando campanha...")
        self.progress_bar.setValue(0)

        parser = self.container.get_parser()
        parser_metrics = getattr(parser, "get_cache_metrics", lambda: {"hits": 0, "misses": 0})()
        record_cache_stats(int(parser_metrics.get("hits", 0)), int(parser_metrics.get("misses", 0)))

        self.sync_thread = DataSyncThread(
            self.pwcgfc_path,
            campaign,
            processor_factory=self.container.create_processor,
            parent=self,
        )

        self.sync_thread.data_loaded.connect(self._on_data_loaded, Qt.QueuedConnection)
        self.sync_thread.error_occurred.connect(self._on_sync_error, Qt.QueuedConnection)
        self.sync_thread.progress.connect(self.progress_bar.setValue, Qt.QueuedConnection)

        self.sync_thread.finished.connect(lambda: self._set_ui_busy(False), Qt.QueuedConnection)

        self.sync_thread.start()

    def _on_data_loaded(self, data: Dict[str, Any]) -> None:
        self.current_data = data or {}
        logger.info("Dados da campanha carregados, atualizando abas...")

        # Aba Missões (validadas uma única vez na entrada do serviço)
        self._validated_missions = self.mission_validation_service.validate(
            self.current_data.get("missions", []) or []
        )
        self.missions_tab.set_missions(self._validated_missions)

        # Aba Ases
        self.aces_tab.set_aces(self.current_data.get("aces", []) or [])

        campaign: str = self.campaign_combo.currentText().strip()

        # País e medalhas do Personnel
        pilot_name = ((self.current_data.get("pilot", {}) or {}).get("name", "") or "").strip()
        personnel_info = self.personnel_resolution_service.resolve(campaign, pilot_name)
        country_code = personnel_info.country_code
        display_name = personnel_info.display_name
        earned_ids = set(personnel_info.earned_medal_ids)

        # Aba Medalhas (carregamento lazy + atualização única de contexto)
        self.medals_tab.set_context(country_code, display_name, earned_ids)
        self._medals_dirty = False

        # Aba Esquadrão
        self.squadron_tab.set_country(country_code)
        self.squadron_tab.set_squadron(self.current_data.get("squadron", []) or [])

        # Aba Perfil
        pilot: str = (self.current_data.get("pilot", {}) or {}).get("name", "N/A")

        if hasattr(self.profile_tab, "set_context"):
            self.profile_tab.set_context(campaign, pilot)
            self.profile_tab.load_from_settings()

        first_dt: datetime = self._first_mission_date() or datetime(self.profile_tab.MIN_ENLIST_YEAR, 1, 1)
        self.profile_tab.set_recruitment_reference_date(first_dt)

        last_dt: Optional[datetime] = self._last_mission_date()
        self.profile_tab.update_reference_date(last_dt)

        roundel_label: str = self._roundel_display_label(country_code, display_name)
        self.profile_tab.set_roundel(country_code, roundel_label)

        self._update_profile_from_data(country_code)
        self.profile_tab.set_ribbons(country_code, earned_ids)

        squadron_name: str = (self.current_data.get("pilot", {}) or {}).get("squadron", "N/A")
        self.squadron_tab.set_squad_overview(squadron_name)

        self.statusBar().showMessage("Dados carregados com sucesso.", 4000)

    def _on_sync_error(self, msg: str) -> None:
        notify_error(f"Erro de sincronização: {msg}")
        logger.error("Erro de sincronização: %s", msg)
        self.statusBar().showMessage("Falha ao sincronizar dados.", 4000)

    def _on_tab_changed(self, index: int) -> None:
        tab_t0 = time.perf_counter()
        success = True
        try:
            if self.tabs.widget(index) is self.medals_tab and (self._medals_dirty or not self._medals_loaded_once):
                self.medals_tab.reload()
                self._medals_loaded_once = True
                self._medals_dirty = False
        except AttributeError:
            success = False
            logger.warning("Falha ao recarregar aba de Medalhas ao mudar de aba")
        finally:
            duration_ms = (time.perf_counter() - tab_t0) * 1000.0
            tab_name = self.tabs.tabText(index) if 0 <= index < self.tabs.count() else "unknown"
            record_action_duration(structured_logger, f"tab_switch:{tab_name}", duration_ms, success=success)

    def _mark_medals_dirty(self) -> None:
        self._medals_dirty = True

    def _on_mission_selected(self, index: int, mission: Dict[str, Any]) -> None:
        self.selected_mission_index = index
        self.profile_tab.update_reference_date(self._last_mission_date())
        logger.debug("Missão selecionada: índice %s", index)

    # ---------------- Resolução de dados ----------------

    def _update_profile_from_data(self, country_code: str) -> None:
        pilot: Dict[str, Any] = self.current_data.get("pilot", {}) or {}
        name: str = pilot.get("name", "N/A")
        squadron: str = pilot.get("squadron", "N/A")
        total_missions: int = int(pilot.get("total_missions", 0) or 0)

        if hasattr(self.profile_tab, "set_profile_labels"):
            self.profile_tab.set_profile_labels(name, squadron, total_missions)
        else:
            # Fallback: labels diretas (se existirem)
            try:
                self.profile_tab.pilot_name_label.setText(name or "N/A")
                self.profile_tab.squadron_name_label.setText(squadron or "N/A")
                self.profile_tab.total_missions_label.setText(str(total_missions or 0))
            except AttributeError:
                logger.warning("Não foi possível atualizar labels do perfil")

        rank: str = self._resolve_player_rank(name, self.current_data.get("squadron", []) or [])
        self.profile_tab.set_rank_with_insignia(
            rank_name=rank,
            country_folder=(country_code or "GERMANY").lower(),
        )

    @staticmethod
    def _resolve_player_rank(pilot_name: str, squadron_list: List[Dict[str, Any]]) -> str:
        name_norm: str = (pilot_name or "").strip().lower()
        for m in squadron_list or []:
            try:
                member_name: str = (m.get("name", "") or "").strip().lower()
                if member_name == name_norm and m.get("rank"):
                    return str(m.get("rank"))
            except (KeyError, TypeError, AttributeError):
                continue
        return "N/A"

    @staticmethod
    def _roundel_display_label(country_code: str, display_name: str) -> str:
        c: str = (country_code or "").strip().upper()
        if c == "BRITAIN":
            return "Great Britain"
        if c == "BELGIAN":
            return "Belgium"
        return display_name or "Germany"

    # ---------------- Datas de missões ----------------

    def _first_mission_date(self) -> Optional[datetime]:
        dates: List[datetime] = []
        for m in self._validated_missions:
            d = self._parse_any_date(m.date)
            if d:
                dates.append(d)
        return min(dates) if dates else None

    def _last_mission_date(self) -> Optional[datetime]:
        dates: List[datetime] = []
        for m in self._validated_missions:
            d = self._parse_any_date(m.date)
            if d:
                dates.append(d)
        return max(dates) if dates else None

    @staticmethod
    def _parse_any_date(s: str) -> Optional[datetime]:
        s = (s or "").strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y%m%d"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None

    # ---------------- Persistência ----------------

    def _load_saved_settings(self) -> None:
        saved_path: str = str(self.settings.value("pwcgfc_path", "") or "")
        if saved_path and Path(saved_path).exists():
            self.pwcgfc_path = saved_path
            self.container.set_pwcgfc_path(self.pwcgfc_path)
            self._full_path_text = f"Caminho: {saved_path}"
            self._update_elided_path_label()
            self._load_campaigns()

            try:
                self.insert_squads_tab.set_pwcgfc_path(self.pwcgfc_path)
            except AttributeError:
                pass
            try:
                self.input_medals_tab.set_pwcgfc_path(self.pwcgfc_path)
            except AttributeError:
                pass
        else:
            self._full_path_text = ""
            self._update_elided_path_label()
