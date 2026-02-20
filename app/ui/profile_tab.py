# -*- coding: utf-8 -*-

# ===================================================================
# Wing Mate - app/ui/profile_tab.py
# Perfil do Piloto com retrato, roundel, patente e condecorações
#
# Melhoria de UI aplicada:
# - Condecorações agora usam FlowLayout (wrap) em vez de QHBoxLayout,
#   evitando scroll horizontal e melhorando a leitura quando há muitos ribbons.
# ===================================================================

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Tuple, Set, List

from datetime import datetime

from PyQt5.QtCore import Qt, QDate, QSettings, QSize, QRect, QPoint
from PyQt5.QtGui import QPixmap, QIcon, QMouseEvent
from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QMessageBox,
    QFrame,
    QScrollArea,
    QWidget as QtWidget,
    QToolButton,
    QDialog,
    QDialogButtonBox,
    QCalendarWidget,
    QDateEdit,
    QLayout,
    QLayoutItem,
    QSizePolicy,
)

import logging

from app.ui.error_feedback import show_actionable_error
from utils.observability import Events, emit_event
from utils.structured_logger import StructuredLogger

logger = logging.getLogger("IL2CampaignAnalyzer")
structured_logger = StructuredLogger("IL2CampaignAnalyzer")


class FlowLayout(QLayout):
    """
    Layout estilo 'flow' (quebra linha automática), similar a um grid flexível.

    Implementação baseada no exemplo clássico do Qt (adaptado para PyQt5),
    mantendo o código pequeno e previsível.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        margin: int = 0,
        h_spacing: int = 8,
        v_spacing: int = 8,
    ) -> None:
        super().__init__(parent)
        self._items: List[QLayoutItem] = []
        self._h_spacing = int(h_spacing)
        self._v_spacing = int(v_spacing)
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item: QLayoutItem) -> None:
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self) -> Qt.Orientations:
        return Qt.Orientations(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        left, top, right, bottom = self.getContentsMargins()
        size += QSize(left + right, top + bottom)
        return size

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        left, top, right, bottom = self.getContentsMargins()
        effective = rect.adjusted(left, top, -right, -bottom)

        x = effective.x()
        y = effective.y()
        line_height = 0

        for item in self._items:
            w = item.widget()
            if w is not None and not w.isVisible():
                continue

            hint = item.sizeHint()
            next_x = x + hint.width() + self._h_spacing

            if next_x - self._h_spacing > effective.right() and line_height > 0:
                x = effective.x()
                y = y + line_height + self._v_spacing
                next_x = x + hint.width() + self._h_spacing
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))

            x = next_x
            line_height = max(line_height, hint.height())

        return (y + line_height - rect.y()) + bottom


class BirthDateEdit(QDateEdit):
    """QDateEdit customizado com diálogo de calendário dedicado."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setCalendarPopup(False)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        super().mousePressEvent(e)
        self._open_calendar_dialog()

    def _open_calendar_dialog(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr("Selecionar Data de Nascimento"))

        cal = QCalendarWidget(dlg)
        cal.setGridVisible(True)
        cal.setMinimumDate(self.minimumDate())
        cal.setMaximumDate(self.maximumDate())

        cur = self.date()
        if cur.isValid():
            cal.setSelectedDate(cur)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=dlg)

        lay = QVBoxLayout(dlg)
        lay.addWidget(cal)
        lay.addWidget(btns)

        def accept():
            self.setDate(cal.selectedDate())
            dlg.accept()

        btns.accepted.connect(accept)
        btns.rejected.connect(dlg.reject)
        dlg.exec_()


class ProfileTab(QWidget):
    """Aba de perfil do piloto com retrato, roundel, patente e condecorações."""

    MIN_ENLIST_YEAR = 1916
    MIN_AGE = 18
    DEFAULT_MAX_RECRUIT_AGE = 45

    FRAME_W = 311
    FRAME_H = 466
    AVATAR_MAX_W = 260
    AVATAR_MAX_H = 380

    MAX_BIRTHPLACE = 100
    MAX_BIO = 2000
    SCHEMA_VERSION = 1

    def __init__(self, settings: Optional[QSettings] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.settings = settings or QSettings("IL2CampaignAnalyzer", "Settings")

        self._ref_date: Optional[datetime] = None
        self.loaded_ok = False
        self.loading = False

        self._campaign_key = "default"
        self._pilot_key = "default"
        self._recruit_ref_year = self.MIN_ENLIST_YEAR
        self._max_recruit_age = int(self.settings.value("profile/max_recruit_age", self.DEFAULT_MAX_RECRUIT_AGE))

        self.pilot_name_label = QLabel("N/A")
        self.squadron_name_label = QLabel("N/A")
        self.total_missions_label = QLabel("0")

        self.roundel_image_label = QLabel()
        self.roundel_image_label.setAlignment(Qt.AlignCenter)
        self.roundel_image_label.setFixedSize(136, 137)

        self.roundel_text_label = QLabel("N/A")
        self.roundel_text_label.setAlignment(Qt.AlignCenter)

        self.rank_image_label = QLabel()
        self.rank_image_label.setAlignment(Qt.AlignCenter)
        self.rank_image_label.setFixedSize(96, 160)

        self.rank_text_label = QLabel("N/A")
        self.rank_text_label.setAlignment(Qt.AlignCenter)

        self.portrait_container: Optional[QFrame] = None
        self.avatar_label: Optional[QLabel] = None
        self.frame_label: Optional[QLabel] = None

        self.dob_edit = BirthDateEdit()
        self.age_label = QLabel("N/A")
        self.birthplace_edit = QLineEdit()
        self.bio_edit = QTextEdit()
        self.btn_save: Optional[QPushButton] = None

        # Condecorações (agora com FlowLayout)
        self._ribbons_scroll: Optional[QScrollArea] = None
        self._ribbons_holder: Optional[QtWidget] = None
        self._ribbons_layout: Optional[FlowLayout] = None

        # Tamanho menor ajuda bastante na densidade e evita UI "gigante"
        self._ribbon_icon_size = QSize(96, 96)

        self._build_ui()
        self._connect_signals()
        self._configure_dob_bounds()
        self.load_from_settings()

    # ---------------- Keys/paths ----------------

    @staticmethod
    def _slug(s: str) -> str:
        s = (s or "").strip().lower()
        s = re.sub(r"\s+", "_", s)
        s = re.sub(r"[^a-z0-9_\-\.\:\/]", "", s)
        return s or "default"

    def set_context(self, campaign_name: str, pilot_name: str) -> None:
        self._campaign_key = self._slug(campaign_name)
        self._pilot_key = self._slug(pilot_name)
        logger.info("Contexto definido: campanha=%s, piloto=%s", self._campaign_key, self._pilot_key)

    def _prefix(self) -> str:
        return f"campaigns/{self._campaign_key}/profiles/{self._pilot_key}"

    @staticmethod
    def _icons_base_dir() -> Path:
        return Path(__file__).resolve().parents[1] / "assets" / "icons"

    @staticmethod
    def _medals_base_dir() -> Path:
        return Path(__file__).resolve().parents[1] / "assets" / "medals"

    @staticmethod
    def _ranks_base_dir() -> Path:
        return Path(__file__).resolve().parents[1] / "assets" / "ranks"

    def _get_asset_path(self, name: str) -> Path:
        p = self._icons_base_dir() / name
        return p if p.exists() else Path()

    # ---------------- UI ----------------

    def _build_ui(self):
        outer = QHBoxLayout(self)

        portrait_group = QGroupBox(self.tr("Retrato"))
        pv = QVBoxLayout(portrait_group)

        self.portrait_container = QFrame()
        self.portrait_container.setFixedSize(self.FRAME_W, self.FRAME_H)
        self.portrait_container.setStyleSheet("background: transparent;")

        self.avatar_label = QLabel(self.portrait_container)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setStyleSheet("background-color: #202020; border: 1px solid #444;")

        ax = (self.FRAME_W - self.AVATAR_MAX_W) // 2
        ay = (self.FRAME_H - self.AVATAR_MAX_H) // 2
        self.avatar_label.setGeometry(ax, ay, self.AVATAR_MAX_W, self.AVATAR_MAX_H)

        self.frame_label = QLabel(self.portrait_container)
        self.frame_label.setAlignment(Qt.AlignCenter)
        self.frame_label.setGeometry(0, 0, self.FRAME_W, self.FRAME_H)

        self._load_frame()
        pv.addWidget(self.portrait_container)

        btns = QHBoxLayout()
        btn_avatar = QPushButton(self.tr("Escolher Avatar"))
        btn_avatar.clicked.connect(self._choose_avatar)
        btn_clear = QPushButton(self.tr("Remover Avatar"))
        btn_clear.clicked.connect(self._clear_avatar)
        btns.addWidget(btn_avatar)
        btns.addWidget(btn_clear)
        pv.addLayout(btns)

        outer.addWidget(portrait_group)

        info_group = QGroupBox(self.tr("Dados do Piloto"))
        info_hbox = QHBoxLayout(info_group)

        rank_panel = QFrame()
        rank_panel.setFixedWidth(180)
        rp_v = QVBoxLayout(rank_panel)
        rp_v.setContentsMargins(0, 8, 12, 0)
        rp_v.setSpacing(6)

        emblem_holder = QWidget()
        emblem_v = QVBoxLayout(emblem_holder)
        emblem_v.setContentsMargins(0, 0, 0, 0)
        emblem_v.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        emblem_v.addWidget(self.roundel_image_label)
        emblem_v.addWidget(self.roundel_text_label)

        rank_pix_holder = QWidget()
        rank_pix_v = QVBoxLayout(rank_pix_holder)
        rank_pix_v.setContentsMargins(0, 10, 0, 0)
        rank_pix_v.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        rank_pix_v.addWidget(self.rank_image_label)
        rank_pix_v.addWidget(self.rank_text_label)

        rp_v.addWidget(emblem_holder, 0, Qt.AlignTop)
        rp_v.addWidget(rank_pix_holder, 0, Qt.AlignTop)
        rp_v.addStretch(1)

        form_right = QFormLayout()
        form_right.addRow(self.tr("Nome:"), self.pilot_name_label)
        form_right.addRow(self.tr("Esquadrão:"), self.squadron_name_label)
        form_right.addRow(self.tr("Missões Voadas:"), self.total_missions_label)

        self.dob_edit.setDisplayFormat("dd/MM/yyyy")
        form_right.addRow(self.tr("Data de Nascimento:"), self.dob_edit)
        form_right.addRow(self.tr("Idade (últ. missão):"), self.age_label)

        self.birthplace_edit.setMaxLength(self.MAX_BIRTHPLACE)
        form_right.addRow(self.tr("Local de Nascimento:"), self.birthplace_edit)

        self.bio_edit.setPlaceholderText(self.tr("Biografia do piloto..."))
        self.bio_edit.setFixedHeight(120)
        form_right.addRow(self.tr("Biografia:"), self.bio_edit)

        ribbons_group = QGroupBox(self.tr("Condecorações"))
        rv = QVBoxLayout(ribbons_group)

        self._ribbons_scroll = QScrollArea()
        self._ribbons_scroll.setWidgetResizable(True)
        self._ribbons_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._ribbons_holder = QtWidget()
        self._ribbons_holder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # FlowLayout (wrap)
        self._ribbons_layout = FlowLayout(self._ribbons_holder, margin=0, h_spacing=8, v_spacing=8)
        self._ribbons_holder.setLayout(self._ribbons_layout)

        self._ribbons_scroll.setWidget(self._ribbons_holder)
        rv.addWidget(self._ribbons_scroll)

        form_right.addRow(ribbons_group)

        # Botão salvar desabilitado inicialmente
        self.btn_save = QPushButton(self.tr("Salvar Perfil"))
        self.btn_save.clicked.connect(self.save_to_settings)
        self.btn_save.setEnabled(False)
        form_right.addRow("", self.btn_save)

        info_hbox.addWidget(rank_panel)

        right_holder = QWidget()
        right_holder.setLayout(form_right)
        info_hbox.addWidget(right_holder, 1)

        outer.addWidget(info_group, stretch=1)

    def _connect_signals(self):
        self.dob_edit.dateChanged.connect(self._update_age_label)
        self.dob_edit.dateChanged.connect(self._update_save_button)
        self.birthplace_edit.textChanged.connect(self._update_save_button)
        self.bio_edit.textChanged.connect(self._update_save_button)

    # ---------------- Assets (frame/avatar/roundel/rank) ----------------

    def _load_frame(self):
        if not self.frame_label:
            return

        frame_path = self._get_asset_path("char_frame.png")
        if not frame_path:
            self.frame_label.setText(self.tr("Frame ausente"))
            self.frame_label.setStyleSheet("color:#888; border:1px dashed #666;")
            return

        pm = QPixmap(str(frame_path))
        if pm.isNull():
            self.frame_label.setText(self.tr("Frame ausente"))
            self.frame_label.setStyleSheet("color:#888; border:1px dashed #666;")
            return

        self.frame_label.setStyleSheet("")
        self.frame_label.setText("")
        self.frame_label.setPixmap(pm.scaled(self.FRAME_W, self.FRAME_H, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.frame_label.raise_()

    def _choose_avatar(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("Escolher Avatar"), "", self.tr("Imagens (*.png *.jpg *.jpeg)"))
        if not path:
            return
        try:
            self._set_avatar_pixmap(Path(path))
            self.settings.setValue(f"{self._prefix()}/avatar_path", path)
        except (OSError, ValueError):
            QMessageBox.warning(self, self.tr("Erro"), self.tr("Não foi possível carregar a imagem."))

    def _clear_avatar(self):
        if self.avatar_label:
            self.avatar_label.clear()
        self.settings.remove(f"{self._prefix()}/avatar_path")
        if self.frame_label:
            self.frame_label.raise_()

    def _set_avatar_pixmap(self, path: Path):
        if not self.avatar_label:
            return
        pm = QPixmap(str(path))
        if pm.isNull():
            raise ValueError("Imagem inválida")
        pm = pm.scaled(self.AVATAR_MAX_W, self.AVATAR_MAX_H, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.avatar_label.setPixmap(pm)
        if self.frame_label:
            self.frame_label.raise_()

    def set_roundel(self, country_code: str, display_name: Optional[str] = None):
        code = (country_code or "").strip().upper()
        name_map = {"GERMANY": "Germany", "BRITAIN": "Great Britain", "USA": "USA", "FRANCE": "France", "BELGIAN": "Belgium"}
        label = display_name or name_map.get(code, "Germany")
        self.roundel_text_label.setText(label)

        stem_map = {"GERMANY": "theme_german", "BRITAIN": "theme_rfc", "USA": "theme_american", "FRANCE": "theme_french", "BELGIAN": "theme_belgium"}
        stem = stem_map.get(code, "theme_german")
        base = self._icons_base_dir()
        img_path = self._find_image_file(base, stem)

        if not img_path:
            self.roundel_image_label.setText(self.tr("Sem roundel"))
            self.roundel_image_label.setStyleSheet("color:#888;")
            return

        pm = QPixmap(str(img_path))
        if pm.isNull():
            self.roundel_image_label.setText(self.tr("Sem roundel"))
            self.roundel_image_label.setStyleSheet("color:#888;")
            return

        pm = pm.scaled(self.roundel_image_label.width(), self.roundel_image_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.roundel_image_label.setStyleSheet("")
        self.roundel_image_label.setText("")
        self.roundel_image_label.setPixmap(pm)

    def _find_image_file(self, base_dir: Path, stem: str) -> Optional[Path]:
        for ext in (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"):
            p = base_dir / f"{stem}{ext}"
            if p.exists():
                return p

        alt_stems = [f"{stem}_roundel", f"roundel_{stem}", stem.lower(), stem.title()]
        for s in alt_stems:
            for ext in (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"):
                p = base_dir / f"{s}{ext}"
                if p.exists():
                    return p
        return None

    def set_rank(self, rank: str):
        self.set_rank_with_insignia(rank_name=rank, country_folder="germany")

    def set_rank_with_insignia(self, rank_name: str, country_folder: str = "germany"):
        display = rank_name or "N/A"
        self.rank_text_label.setText(display)

        key_raw = (rank_name or "").strip()
        if not key_raw:
            self.rank_image_label.clear()
            return

        key_norm = key_raw.lower().replace(" ", "_").replace("-", "_")
        base = self._ranks_base_dir() / country_folder
        img_path = self._find_image_file(base, key_norm)

        if not img_path:
            self.rank_image_label.setText(self.tr("Imagem não encontrada"))
            self.rank_image_label.setStyleSheet("color:#888;")
            return

        pm = QPixmap(str(img_path))
        if pm.isNull():
            self.rank_image_label.setText(self.tr("Imagem não encontrada"))
            self.rank_image_label.setStyleSheet("color:#888;")
            return

        pm = pm.scaled(self.rank_image_label.width(), self.rank_image_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.rank_image_label.setStyleSheet("")
        self.rank_image_label.setText("")
        self.rank_image_label.setPixmap(pm)

    # ---------------- Profile setters ----------------

    def set_profile_labels(self, name: str, squadron: str, total_missions: int):
        self.pilot_name_label.setText(name or "N/A")
        self.squadron_name_label.setText(squadron or "N/A")
        self.total_missions_label.setText(str(total_missions or 0))

    def update_reference_date(self, ref_date: Optional[datetime]):
        self._ref_date = ref_date
        self._update_age_label()

    def set_recruitment_reference_date(self, ref_date: Optional[datetime]):
        self._recruit_ref_year = ref_date.year if ref_date else self.MIN_ENLIST_YEAR
        self._configure_dob_bounds()

    # ---------------- DOB bounds/validation ----------------

    def _configure_dob_bounds(self):
        max_year = self.MIN_ENLIST_YEAR - self.MIN_AGE
        min_year = max(1800, self._recruit_ref_year - max(self.MIN_AGE, self._max_recruit_age))

        if min_year > max_year:
            min_year = max_year

        min_date = QDate(min_year, 1, 1)
        max_date = QDate(max_year, 12, 31)
        self.dob_edit.setDateRange(min_date, max_date)

        cur = self.dob_edit.date()
        if not cur.isValid() or cur < min_date or cur > max_date:
            self.dob_edit.setDate(max_date)

    # ---------------- Ribbons (FlowLayout) ----------------

    def _clear_ribbons(self):
        if not self._ribbons_layout:
            return

        while self._ribbons_layout.count():
            item = self._ribbons_layout.takeAt(0)
            if not item:
                continue
            w = item.widget()
            if w:
                w.deleteLater()

    def set_ribbons(self, country_code: str, earned_ids: Optional[Set[str]] = None):
        self._clear_ribbons()

        ids = list(earned_ids or [])
        if not ids:
            if self._ribbons_layout:
                self._ribbons_layout.addWidget(QLabel(self.tr("Sem condecorações registradas.")))
            return

        code = (country_code or "GERMANY").upper()
        base = self._medals_base_dir() / code
        if not base.exists():
            if self._ribbons_layout:
                self._ribbons_layout.addWidget(QLabel(self.tr("Pasta de medalhas ausente.")))
            return

        def _pick_pm(stem: str) -> Optional[QPixmap]:
            for ext in (".png", ".PNG", ".jpg", ".jpeg", ".JPG", ".JPEG"):
                p = base / f"{stem}{ext}"
                pm = QPixmap(str(p))
                if not pm.isNull():
                    return pm

                p = base / f"ribbon_{stem}{ext}"
                pm = QPixmap(str(p))
                if not pm.isNull():
                    return pm
            return None

        for mid in ids:
            pm = _pick_pm(mid)
            if pm is None:
                continue

            scaled_pm = pm.scaled(self._ribbon_icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            btn = QToolButton()
            btn.setIcon(QIcon(scaled_pm))
            btn.setIconSize(self._ribbon_icon_size)
            btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            btn.setAutoRaise(True)
            btn.setToolTip(mid)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedSize(self._ribbon_icon_size.width() + 10, self._ribbon_icon_size.height() + 10)

            if self._ribbons_layout:
                self._ribbons_layout.addWidget(btn)

    # ---------------- Persistence ----------------

    def save_to_settings(self):
        ok, msg = self._validate_profile()
        if not ok:
            QMessageBox.warning(self, self.tr("Validação"), msg)
            return

        try:
            prefix = self._prefix()
            self.settings.setValue(f"{prefix}/schema_version", self.SCHEMA_VERSION)
            self.settings.setValue(f"{prefix}/dob", self.dob_edit.date().toString("yyyy-MM-dd"))
            self.settings.setValue(f"{prefix}/birthplace", self.birthplace_edit.text()[: self.MAX_BIRTHPLACE])
            self.settings.setValue(f"{prefix}/bio", self.bio_edit.toPlainText()[: self.MAX_BIO])
            emit_event(
                structured_logger,
                Events.PROFILE_SAVED,
                campaign_key=self._campaign_key,
                pilot_key=self._pilot_key,
                schema_version=self.SCHEMA_VERSION,
            )
            QMessageBox.information(self, self.tr("Perfil"), self.tr("Dados do perfil salvos."))
        except OSError as e:
            show_actionable_error(
                parent=self,
                title=self.tr("Erro"),
                summary=self.tr("Não foi possível salvar o perfil."),
                action_hint=self.tr("Verifique permissões e espaço em disco antes de tentar novamente."),
                technical_details=str(e),
                file_path=prefix,
            )

    def load_from_settings(self):
        self.loaded_ok = False
        self.loading = True

        try:
            prefix = self._prefix()
            self._load_frame()

            avatar_path = self.settings.value(f"{prefix}/avatar_path", "")
            if avatar_path:
                try:
                    self._set_avatar_pixmap(Path(avatar_path))
                except (OSError, ValueError):
                    pass
            else:
                if self.avatar_label:
                    self.avatar_label.clear()
                if self.frame_label:
                    self.frame_label.raise_()

            dob_str = self.settings.value(f"{prefix}/dob", "")
            if dob_str:
                try:
                    d = datetime.strptime(dob_str, "%Y-%m-%d")
                    self.dob_edit.setDate(QDate(d.year, d.month, d.day))
                except ValueError:
                    self._configure_dob_bounds()
            else:
                self._configure_dob_bounds()

            self.birthplace_edit.setText(self.settings.value(f"{prefix}/birthplace", "")[: self.MAX_BIRTHPLACE])
            self.bio_edit.setPlainText(self.settings.value(f"{prefix}/bio", "")[: self.MAX_BIO])

            self.loaded_ok = True

        except OSError:
            pass

        finally:
            self.loading = False
            self._update_age_label()
            self._update_save_button()

    # ---------------- Validation ----------------

    def _validate_profile(self) -> Tuple[bool, str]:
        qd = self.dob_edit.date()
        dob = datetime(qd.year(), qd.month(), qd.day())

        if dob.date() > datetime.now().date():
            return False, self.tr("A data de nascimento não pode ser futura.")

        birthplace_text = self.birthplace_edit.text()
        if len(birthplace_text) > self.MAX_BIRTHPLACE:
            return False, self.tr(f"Local de nascimento deve ter no máximo {self.MAX_BIRTHPLACE} caracteres.")

        bio_text = self.bio_edit.toPlainText()
        if len(bio_text) > self.MAX_BIO:
            return False, self.tr(f"Biografia deve ter no máximo {self.MAX_BIO} caracteres.")

        return True, ""

    def _update_age_label(self):
        qd = self.dob_edit.date()
        dob = datetime(qd.year(), qd.month(), qd.day())

        if not self._ref_date:
            self.age_label.setText("N/A")
            return

        age = self._compute_age(dob, self._ref_date)
        self.age_label.setText("N/A" if age < 0 else str(age))

    def _update_save_button(self):
        if not self.btn_save:
            return
        ok, _ = self._validate_profile()
        self.btn_save.setEnabled(ok and self.loaded_ok and not self.loading)

    @staticmethod
    def _compute_age(dob: datetime, ref: datetime) -> int:
        if ref.date() < dob.date():
            return -1
        return ref.year - dob.year - ((ref.month, ref.day) < (dob.month, dob.day))
