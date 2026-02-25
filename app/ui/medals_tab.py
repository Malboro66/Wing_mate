# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - app/ui/medals_tab.py
# Modo Grade com QListWidget (IconMode) 262x293 + Lista com botão Editar
#
# Melhorias de UI:
# - Duplo clique abre detalhes (clique simples apenas seleciona)
# - Cache de QPixmap para reduzir travadas ao filtrar/rolar
# ===================================================================

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Union, Tuple

from PyQt5.QtCore import Qt, QSize, QTimer, QEvent
from PyQt5.QtGui import QPixmap, QIcon, QColor, QMouseEvent
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QPushButton,
    QDialog,
    QTextBrowser,
    QDialogButtonBox,
    QListWidget,
    QListWidgetItem,
    QListView,
)

from app.ui.widgets.medal_hover_popup import MedalHoverPopup

logger = logging.getLogger(__name__)


class MedalDescEditor(QDialog):
    def __init__(
        self,
        medal_id: str,
        medal_name: str,
        initial_desc: str,
        base_dir: Path,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Editar descrição - {medal_name}")
        self.medal_id: str = medal_id
        self.medal_name: str = medal_name
        self.base_dir: Path = base_dir

        self.viewer: QTextBrowser = QTextBrowser()
        self.viewer.setPlainText(initial_desc or "")
        self.viewer.setMinimumHeight(220)

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.addWidget(QLabel("Descrição"))
        layout.addWidget(self.viewer)

        btns: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _save(self) -> None:
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            payload: Dict[str, Any] = {
                "id": self.medal_id,
                "name": self.medal_name,
                "descricao": self.viewer.toPlainText().strip(),
            }
            out: Path = self.base_dir / f"{self.medal_id}.json"
            out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            self.accept()
        except (OSError, TypeError, ValueError) as e:
            logger.error("Falha ao salvar descrição da medalha %s: %s", self.medal_id, e)
            QMessageBox.critical(self, "Erro", f"Falha ao salvar descrição: {e}")


class MedalDetailsDialog(QDialog):
    """Janela de detalhes: Nome, Imagem e Informações."""

    def __init__(
        self,
        name: str,
        pixmap: Optional[QPixmap],
        html: str,
        img_size: QSize,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(name or "Medalha")
        self.setMinimumWidth(max(480, img_size.width() + 60))

        layout: QVBoxLayout = QVBoxLayout(self)

        title: QLabel = QLabel(name or "Medalha")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:18px; font-weight:bold; margin:8px 0;")
        layout.addWidget(title)

        img: QLabel = QLabel()
        img.setAlignment(Qt.AlignCenter)
        img.setFixedSize(img_size)
        if pixmap:
            img.setPixmap(pixmap.scaled(img_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            img.setText("Sem imagem")
            img.setStyleSheet("color:#888;")
        layout.addWidget(img)

        info: QTextBrowser = QTextBrowser()
        info.setOpenExternalLinks(False)
        info.setHtml(html or "<i>Sem informações disponíveis.</i>")
        info.setMinimumHeight(260)
        layout.addWidget(info)

        btns: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(self.reject)
        btns.accepted.connect(self.accept)
        btns.button(QDialogButtonBox.Close).clicked.connect(self.close)
        layout.addWidget(btns)


class MedalsTab(QWidget):
    MEDAL_W: int = 262
    MEDAL_H: int = 293

    CARD_HPADDING: int = 12
    GRID_HSPACING: int = 24
    GRID_VSPACING: int = 20

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._country_code: str = "generic"
        self._country_label: QLabel = QLabel("N/A")
        self._earned_ids: Set[str] = set()

        # Controles
        self._mode_combo: Optional[QComboBox] = None
        self._filter_combo: Optional[QComboBox] = None
        self._origin_combo: Optional[QComboBox] = None
        self._search_edit: Optional[QLineEdit] = None
        self._show_all_nations_chk: Optional[QCheckBox] = None
        self._counter_label: Optional[QLabel] = None

        # Visualizadores
        self._icon_list: Optional[QListWidget] = None
        self._table: Optional[QTableWidget] = None

        # Dados
        self._all_items: List[Dict[str, Any]] = []

        # Cache de pixmaps (melhora fluidez na grade)
        self._pixmap_cache: Dict[str, Optional[QPixmap]] = {}
        self._hover_popup: Optional[MedalHoverPopup] = None

        self._build_ui()

    # ---------------- Paths ----------------

    @staticmethod
    def _assets_base() -> Path:
        return Path(__file__).resolve().parents[1] / "assets" / "medals"

    def _desc_dir(self) -> Path:
        return self._assets_base() / "descriptions"

    def _country_dir(self) -> Path:
        base: Path = self._assets_base()
        code = (self._country_code or "generic").strip()
        candidates = [base / code.lower(), base / code.upper(), base / code.title()]
        for c in candidates:
            if c.exists():
                return c
        return candidates[0]

    def _meta_dirs(self) -> List[Path]:
        base: Path = self._assets_base()
        return [base / "meta", base]

    # ---------------- Lifecycle ----------------

    def showEvent(self, e: QEvent) -> None:
        super().showEvent(e)
        QTimer.singleShot(0, self._rebuild_view)

    def reload(self) -> None:
        self._refresh_all_items()
        self._rebuild_view()

        # Navegação por teclado inicia no campo de busca da aba
        self.setFocusProxy(self._search_edit)

    # ---------------- Setters ----------------

    def set_country(self, code: str, display_name: Optional[str] = None) -> None:
        self._country_code = (code or "generic").lower()
        self._country_label.setText(display_name or self._country_code.upper())
        self.reload()

    def set_earned_ids(self, earned_ids: Optional[Set[str]]) -> None:
        self._earned_ids = set(earned_ids or set())
        self.reload()

    def set_context(
        self,
        code: str,
        display_name: Optional[str],
        earned_ids: Optional[Set[str]],
    ) -> None:
        """Atualiza contexto completo com um único reload para reduzir custo de UI."""
        self._country_code = (code or "generic").lower()
        self._country_label.setText(display_name or self._country_code.upper())
        self._earned_ids = set(earned_ids or set())
        self.reload()

    # ---------------- Ribbon helpers ----------------

    @staticmethod
    def _is_ribbon_name(name: str) -> bool:
        n = (name or "").strip().lower()
        return n.endswith(" ribbon") or n.endswith("ribbon") or n.endswith("_ribbon")

    @staticmethod
    def _is_ribbon_id(mid: str) -> bool:
        m = (mid or "").strip().lower()
        return m.endswith(" ribbon") or m.endswith("ribbon") or m.endswith("_ribbon")

    # ---------------- Build UI ----------------

    def _build_ui(self) -> None:
        root: QVBoxLayout = QVBoxLayout(self)

        controls: QHBoxLayout = QHBoxLayout()
        controls.addWidget(QLabel(self.tr("País:")))
        controls.addWidget(self._country_label)

        self._mode_combo = QComboBox()
        self._mode_combo.setAccessibleName("medals_mode_selector")
        self._mode_combo.addItems([self.tr("Grade"), self.tr("Lista")])
        self._mode_combo.currentIndexChanged.connect(self._rebuild_view)
        controls.addSpacing(12)
        controls.addWidget(QLabel(self.tr("Modo:")))
        controls.addWidget(self._mode_combo)

        self._filter_combo = QComboBox()
        self._filter_combo.setAccessibleName("medals_status_selector")
        self._filter_combo.addItems([self.tr("Todas"), self.tr("Conquistadas"), self.tr("Não Conquistadas")])
        self._filter_combo.currentIndexChanged.connect(self._rebuild_view)
        controls.addSpacing(12)
        controls.addWidget(QLabel(self.tr("Status:")))
        controls.addWidget(self._filter_combo)

        self._origin_combo = QComboBox()
        self._origin_combo.setAccessibleName("medals_origin_selector")
        self._origin_combo.addItems([self.tr("Todas"), self.tr("País"), self.tr("Manifesto")])
        self._origin_combo.currentIndexChanged.connect(self._rebuild_view)
        controls.addSpacing(12)
        controls.addWidget(QLabel(self.tr("Origem:")))
        controls.addWidget(self._origin_combo)

        self._show_all_nations_chk = QCheckBox(self.tr("Mostrar todas as nações (manifesto)"))
        self._show_all_nations_chk.setAccessibleName("medals_show_all_nations")
        self._show_all_nations_chk.stateChanged.connect(self.reload)
        controls.addSpacing(12)
        controls.addWidget(self._show_all_nations_chk)

        controls.addStretch(1)

        self._search_edit = QLineEdit()
        self._search_edit.setAccessibleName("medals_search_input")
        self._search_edit.setPlaceholderText(self.tr("Buscar medalha por nome"))
        self._search_edit.textChanged.connect(self._rebuild_view)
        controls.addWidget(self._search_edit)

        root.addLayout(controls)

        info_line: QHBoxLayout = QHBoxLayout()
        self._counter_label = QLabel("0 de 0")
        info_line.addWidget(self._counter_label)
        info_line.addStretch(1)

        refresh_btn = QPushButton(self.tr("Recarregar"))
        refresh_btn.clicked.connect(self.reload)
        info_line.addWidget(refresh_btn)
        root.addLayout(info_line)

        # Grade
        self._icon_list = QListWidget()
        self._icon_list.setAccessibleName("medals_icon_list")
        self._icon_list.setViewMode(QListView.IconMode)
        self._icon_list.setUniformItemSizes(True)
        self._icon_list.setLayoutMode(QListView.Batched)
        self._icon_list.setBatchSize(24)
        self._icon_list.setMovement(QListView.Static)
        self._icon_list.setResizeMode(QListView.Adjust)
        self._icon_list.setIconSize(QSize(self.MEDAL_W, self.MEDAL_H))
        self._icon_list.setGridSize(QSize(self.MEDAL_W + 2 * self.CARD_HPADDING, self.MEDAL_H + 56))
        self._icon_list.setSpacing(self.GRID_HSPACING // 2)
        self._icon_list.setUniformItemSizes(True)
        self._icon_list.setLayoutMode(QListView.Batched)
        self._icon_list.setBatchSize(24)

        # UI change: clique simples seleciona, duplo clique abre detalhes
        self._icon_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._icon_list.itemActivated.connect(self._on_icon_activated)
        self._icon_list.itemDoubleClicked.connect(self._on_icon_activated)
        self._icon_list.itemClicked.connect(self._on_icon_clicked)
        self._icon_list.setMouseTracking(True)
        self._icon_list.mouseMoveEvent = self._on_icon_hover
        self._icon_list.leaveEvent = self._on_icon_leave

        self._hover_popup = MedalHoverPopup(self)

        root.addWidget(self._icon_list)

        # Lista
        self._table = QTableWidget(0, 3)
        self._table.setAccessibleName("medals_table")
        self._table.setHorizontalHeaderLabels([self.tr("Nome"), self.tr("Status"), self.tr("Editar")])
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.setVisible(False)

        root.addWidget(self._table)

        # Precarrega itens uma vez
        self._refresh_all_items()

    # ---------------- Data loading ----------------

    def _load_country_manifest(self) -> List[Dict[str, Any]]:
        cdir: Path = self._country_dir()
        items: List[Dict[str, Any]] = []

        manifest: Path = cdir / "medals.json"
        if manifest.exists():
            try:
                data: Any = json.loads(manifest.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for item in data:
                        name: str = item.get("name") or item.get("id") or ""
                        mid: str = item.get("id") or (item.get("image") or "").split(".")[0]
                        if self._is_ribbon_name(name) or self._is_ribbon_id(mid):
                            continue
                        items.append(
                            {
                                "id": mid,
                                "name": name,
                                "image": str(cdir / item.get("image")) if item.get("image") else "",
                                "desc": item.get("desc") or item.get("descricao") or "",
                                "source": "country",
                            }
                        )
            except (json.JSONDecodeError, OSError) as e:
                logger.debug("Falha ao ler manifest do país (%s). Usando PNGs soltos. %s", manifest, e)

        if not items:
            try:
                for png in sorted(cdir.glob("*.png")):
                    name = png.stem.replace("_", " ").title()
                    mid = png.stem
                    if self._is_ribbon_name(name) or self._is_ribbon_id(mid):
                        continue
                    items.append(
                        {
                            "id": mid,
                            "name": name,
                            "image": str(png),
                            "desc": "",
                            "source": "country",
                        }
                    )
            except OSError as e:
                logger.debug("Falha ao listar PNGs em %s: %s", cdir, e)

        return items

    def _find_manifest_file(self) -> Optional[Path]:
        for d in self._meta_dirs():
            f = Path(d) / "medals.json"
            if f.exists():
                return f
        return None

    def _load_meta_manifest(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        manifest_file = self._find_manifest_file()
        if not manifest_file:
            return items

        try:
            data: Any = json.loads(manifest_file.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                return items

            current_country = self._country_code
            allow_all = bool(self._show_all_nations_chk and self._show_all_nations_chk.isChecked())

            for it in data:
                nome: str = str(it.get("nome", "") or "").strip()
                mid: str = nome.lower().replace(" ", "_")
                if self._is_ribbon_name(nome) or self._is_ribbon_id(mid):
                    continue

                img_rel: str = str(it.get("imagemPath", "") or "").strip()
                desc: str = str(it.get("descricao", "") or "").strip()
                if not nome or not img_rel:
                    continue

                country: str = str(it.get("country", "") or "").strip().lower()
                if not allow_all and country and country != current_country:
                    continue

                items.append(
                    {
                        "id": mid,
                        "name": nome,
                        "img_rel": img_rel,
                        "desc": desc,
                        "source": "manifest",
                    }
                )
        except (json.JSONDecodeError, OSError) as e:
            logger.debug("Falha ao ler manifesto global (%s): %s", manifest_file, e)

        return items

    def _normalize_all_items(self) -> None:
        country_items = self._load_country_manifest()
        meta_items = self._load_meta_manifest()

        normalized: List[Dict[str, Any]] = []
        for it in country_items:
            mid = str(it["id"])
            normalized.append(
                {
                    "id": mid,
                    "name": str(it.get("name", "") or ""),
                    "desc": str(it.get("desc", "") or ""),
                    "image_path": str(it.get("image", "") or ""),
                    "image_is_rel": False,
                    "earned": mid in self._earned_ids,
                    "source": "País",
                }
            )

        for it in meta_items:
            mid = str(it["id"])
            normalized.append(
                {
                    "id": mid,
                    "name": str(it.get("name", "") or ""),
                    "desc": str(it.get("desc", "") or ""),
                    "image_path": str(it.get("img_rel", "") or ""),
                    "image_is_rel": True,
                    "earned": mid in self._earned_ids,
                    "source": "Manifesto",
                }
            )

        self._all_items = normalized

    def _refresh_all_items(self) -> None:
        self._normalize_all_items()
        # Limpa cache quando o catálogo muda (troca de país / manifest settings)
        self._pixmap_cache.clear()

    # ---------------- Filtering ----------------

    def _filtered_items(self) -> List[Dict[str, Any]]:
        if not self._all_items:
            return []

        txt = (self._search_edit.text() if self._search_edit else "").strip().lower()
        status_idx = int(self._filter_combo.currentIndex()) if self._filter_combo else 0
        origin_idx = int(self._origin_combo.currentIndex()) if self._origin_combo else 0

        out: List[Dict[str, Any]] = []
        for it in self._all_items:
            if txt and txt not in it["name"].lower():
                continue

            if status_idx == 1 and not it["earned"]:
                continue
            if status_idx == 2 and it["earned"]:
                continue

            if origin_idx == 1 and it["source"] != "País":
                continue
            if origin_idx == 2 and it["source"] != "Manifesto":
                continue

            if self._is_ribbon_name(it["name"]) or self._is_ribbon_id(it["id"]):
                continue

            out.append(it)

        return out

    # ---------------- Rendering ----------------

    def _rebuild_view(self) -> None:
        items = self._filtered_items()
        total = len(self._all_items)
        shown = len(items)

        if self._counter_label:
            self._counter_label.setText(f"{shown} exibidas de {total}")

        is_grid = True
        if self._mode_combo:
            is_grid = self._mode_combo.currentIndex() == 0

        if is_grid:
            self._table.setVisible(False)
            self._icon_list.setVisible(True)
            self._render_icon_list(items)
        else:
            self._icon_list.setVisible(False)
            self._table.setVisible(True)
            self._render_table(items)

    def _make_placeholder(self) -> QPixmap:
        pm = QPixmap(self.MEDAL_W, self.MEDAL_H)
        pm.fill(Qt.transparent)
        return pm

    def _resolve_pixmap(self, path_str: str, is_relative: bool) -> Optional[QPixmap]:
        if not path_str:
            return None

        p = Path(path_str)
        full = p if p.is_absolute() or not is_relative else (self._assets_base() / p)

        key = str(full)
        if key in self._pixmap_cache:
            return self._pixmap_cache[key]

        pm = QPixmap(str(full))
        if pm.isNull():
            self._pixmap_cache[key] = None
            return None

        self._pixmap_cache[key] = pm
        return pm

    def _render_icon_list(self, items: List[Dict[str, Any]]) -> None:
        self._icon_list.clear()

        if not items:
            empty = QListWidgetItem("Nenhuma medalha corresponde aos filtros/busca.")
            empty.setFlags(Qt.NoItemFlags)
            self._icon_list.addItem(empty)
            return

        for it in items:
            pm = self._resolve_pixmap(it["image_path"], it["image_is_rel"]) or self._make_placeholder()
            icon = QIcon(pm)
            text = it["name"] or "Nome da medalha"

            item = QListWidgetItem(icon, text)
            item.setToolTip(it.get("desc", "") or "")
            item.setSizeHint(QSize(self.MEDAL_W + 2 * self.CARD_HPADDING, self.MEDAL_H + 56))
            item.setData(Qt.UserRole, it)

            if it["earned"]:
                item.setBackground(QColor(63, 185, 80, 35))

            self._icon_list.addItem(item)

    def _render_table(self, items: List[Dict[str, Any]]) -> None:
        self._table.setRowCount(len(items))

        for r, it in enumerate(items):
            self._table.setItem(r, 0, QTableWidgetItem(it["name"]))
            status_item = QTableWidgetItem("Conquistada" if it["earned"] else "Não conquistada")
            self._table.setItem(r, 1, status_item)

            btn = QPushButton("Editar")
            btn.clicked.connect(lambda _=False, rec=it: self._open_editor(rec))
            self._table.setCellWidget(r, 2, btn)

    # ---------------- Descrições externas ----------------

    def _load_external_description_obj(self, medal_id: str) -> Optional[Dict[str, Any]]:
        desc_file = self._desc_dir() / f"{medal_id}.json"
        if not desc_file.exists():
            return None
        try:
            return json.loads(desc_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.debug("Falha ao ler descrição externa %s: %s", desc_file, e)
            return None

    def _build_details_html(self, rec: Dict[str, Any]) -> str:
        obj = self._load_external_description_obj(rec["id"])
        if obj:
            desc = str(obj.get("descricao", "") or "").strip()
            if desc:
                return f"<p>{desc.replace(chr(10), '<br>')}</p>"

            blocks: List[str] = []
            resumo = str(obj.get("resumo", "") or "").strip()
            if resumo:
                blocks.append(f"<p>{resumo}</p>")

            hist = obj.get("historia") or {}
            if isinstance(hist, dict):
                cri = hist.get("criacao") or {}
                if isinstance(cri, dict):
                    linhas = []
                    if cri.get("data"):
                        linhas.append(f"Criação: {cri.get('data')}")
                    if cri.get("local"):
                        linhas.append(f"Local: {cri.get('local')}")
                    if cri.get("instituidor"):
                        linhas.append(f"Instituidor: {cri.get('instituidor')}")
                    if cri.get("contexto"):
                        linhas.append(f"Contexto: {cri.get('contexto')}")
                    if linhas:
                        blocks.append("<b>Criação</b><br>" + "<br>".join(linhas))

            if blocks:
                return "<div>" + "<br><br>".join(blocks) + "</div>"

        if rec.get("desc"):
            return f"<p>{str(rec['desc']).replace(chr(10), '<br>')}</p>"

        return "<i>Sem informações disponíveis.</i>"

    # ---------------- Actions ----------------

    def _open_editor(self, rec: Dict[str, Any]) -> None:
        initial = rec.get("desc", "") or ""
        dlg = MedalDescEditor(rec["id"], rec["name"], initial, self._desc_dir(), self)
        if dlg.exec_() == QDialog.Accepted:
            obj = self._load_external_description_obj(rec["id"]) or {}
            rec["desc"] = str(obj.get("descricao", "") or rec.get("desc", "") or "")
            self._rebuild_view()

    def _open_details(self, rec: Dict[str, Any]) -> None:
        pm = self._resolve_pixmap(rec["image_path"], rec["image_is_rel"]) or self._make_placeholder()
        html = self._build_details_html(rec)
        dlg = MedalDetailsDialog(rec.get("name", "Medalha"), pm, html, QSize(self.MEDAL_W, self.MEDAL_H), self)
        dlg.exec_()

    def _on_icon_activated(self, item: QListWidgetItem) -> None:
        rec = item.data(Qt.UserRole) or {}
        if rec:
            self._open_details(rec)

    def _on_icon_clicked(self, item: QListWidgetItem) -> None:
        # Clique simples: apenas seleciona (mantém comportamento mais previsível na grade)
        # Mantido como hook caso queira exibir preview/infos no futuro sem abrir diálogo.
        _ = item  # no-op

    def _on_icon_hover(self, event: QMouseEvent) -> None:
        if not self._icon_list:
            return

        item = self._icon_list.itemAt(event.pos())
        if item and self._hover_popup:
            rec = item.data(Qt.UserRole) or {}
            pm = self._resolve_pixmap(rec.get("image_path", ""), rec.get("image_is_rel", False))
            if pm:
                self._hover_popup.schedule(
                    pm,
                    rec.get("name", ""),
                    self._icon_list.mapToGlobal(event.pos()),
                )
            else:
                self._hover_popup.cancel()
        elif self._hover_popup:
            self._hover_popup.cancel()

        QListWidget.mouseMoveEvent(self._icon_list, event)

    def _on_icon_leave(self, event: QEvent) -> None:
        if self._hover_popup:
            self._hover_popup.cancel()
        if self._icon_list:
            QListWidget.leaveEvent(self._icon_list, event)
