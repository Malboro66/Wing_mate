# -*- coding: utf-8 -*-

from typing import List, Dict, Optional, Any, Union, Set
from pathlib import Path
import json
import html
import logging  # <-- Importação adicionada

from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPixmap, QTransform, QColor, QFont, QMouseEvent
from app.application.viewmodels import SquadronViewModel
from app.ui.design_system import DSStyles, DSStates, DSSpacing, apply_section_group
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QToolTip, QLineEdit, QCheckBox
)

logger = logging.getLogger(__name__)  # <-- Instância do logger adicionada


def _esc(s: str) -> str:
    return html.escape(str(s or ""))


class RankIconLabel(QLabel):
    """QLabel com tooltip retardado (2s) para exibir o nome da patente apenas após hover."""
    def __init__(self, rank_text: str, delay_ms: int = 2000, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._rank_text: str = rank_text or "N/A"
        self._delay_ms: int = max(0, int(delay_ms))
        self._timer: QTimer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._show_tooltip)

    def enterEvent(self, event: QMouseEvent) -> None:
        if self._delay_ms > 0:
            self._timer.start(self._delay_ms)
        else:
            self._show_tooltip()
        super().enterEvent(event)

    def leaveEvent(self, event: QMouseEvent) -> None:
        if self._timer.isActive():
            self._timer.stop()
        QToolTip.hideText()
        super().leaveEvent(event)

    def _show_tooltip(self) -> None:
        global_pos: QPoint = self.mapToGlobal(QPoint(self.width() // 2, self.height() // 2))
        QToolTip.showText(global_pos, self._rank_text, self)


class SquadronTab(QWidget):
    """
    Aba de Esquadrão com:
    - Cabeçalho (emblema + painel "Histórico e Dados") lido de assets/squadrons/meta conforme o esquadrão do player
    - Tabela de pessoal: patente como imagem + tooltip, ordenação por posto (maior→menor) e status colorido
    """

    RANK_MAX_W: int = 140
    RANK_MAX_H: int = 110

    EMBLEM_W: int = 360
    EMBLEM_H: int = 240

    RANK_ORDER: Dict[str, List[str]] = {
        "germany": [
            "kommandeur", "kommander", "hauptmann",
            "oberleutnant", "leutnant",
            "feldwebel", "unteroffizier", "gefreiter", "flieger"
        ],
        "britain": [
            "major", "captain", "lieutenant", "1st_lieutenant", "first_lieutenant",
            "2nd_lieutenant", "second_lieutenant",
            "sergeant", "corporal", "airman"
        ],
        "france": [
            "commandant", "capitaine", "lieutenant", "sous_lieutenant",
            "adjudant_chef", "adjudant", "sergent_chef", "sergent",
            "caporal_chef", "caporal"
        ],
        "usa": [
            "captain", "first_lieutenant", "1st_lieutenant", "second_lieutenant", "2nd_lieutenant",
            "sergeant", "corporal", "private"
        ],
        "belgian": [
            "commandant", "capitaine", "lieutenant", "sous_lieutenant",
            "adjudant_chef", "adjudant", "sergent_chef", "sergent",
            "caporal_chef", "caporal"
        ],
    }

    STATUS_COLORS: Dict[str, QColor] = {
        "ativo": QColor(0, 140, 0),
        "active": QColor(0, 140, 0),
        "ferido": QColor(220, 120, 0),
        "wounded": QColor(220, 120, 0),
        "injured": QColor(220, 120, 0),
        "desaparecido": QColor(120, 60, 160),
        "mia": QColor(120, 60, 160),
        "morto": QColor(200, 0, 0),
        "kia": QColor(200, 0, 0),
        "killed": QColor(200, 0, 0),
        "prisioneiro": QColor(120, 70, 40),
        "pow": QColor(120, 70, 40),
        "captured": QColor(120, 70, 40),
        "hospital": QColor(30, 100, 200),
        "hospitalized": QColor(30, 100, 200),
        "licenca": QColor(90, 110, 130),
        "licença": QColor(90, 110, 130),
        "leave": QColor(90, 110, 130),
        "rest": QColor(90, 110, 130),
    }

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._country_folder: str = "germany"
        self._current_squad_name: str = ""
        self._vm: SquadronViewModel = SquadronViewModel()

        root: QVBoxLayout = QVBoxLayout(self)

        # Cabeçalho (emblema + texto organizado)
        self.header_group: QGroupBox = QGroupBox(self.tr("Esquadrão"))
        apply_section_group(self.header_group)
        header_h: QHBoxLayout = QHBoxLayout(self.header_group)

        self.emblem_label: QLabel = QLabel(self.tr("Sem emblema"))
        self.emblem_label.setAlignment(Qt.AlignCenter)
        self.emblem_label.setFixedSize(self.EMBLEM_W, self.EMBLEM_H)
        self.emblem_label.setStyleSheet(DSStyles.PANEL_PLACEHOLDER)
        header_h.addWidget(self.emblem_label)

        text_panel: QWidget = QWidget()
        text_v: QVBoxLayout = QVBoxLayout(text_panel)

        self.title_label: QLabel = QLabel(self.tr("N/A"))
        title_font: QFont = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setWordWrap(True)

        self.details_label: QLabel = QLabel("")
        self.details_label.setWordWrap(True)
        self.details_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.details_label.setTextFormat(Qt.RichText)
        self.details_label.setOpenExternalLinks(True)
        self.details_label.setStyleSheet("font-size: 12pt;")

        text_v.addWidget(self.title_label)

        scroll: QScrollArea = QScrollArea()
        scroll.setWidgetResizable(True)
        summary_holder: QWidget = QWidget()
        sh_v: QVBoxLayout = QVBoxLayout(summary_holder)
        sh_v.addWidget(self.details_label)
        sh_v.addStretch(1)
        scroll.setWidget(summary_holder)
        text_v.addWidget(scroll, 1)

        header_h.addWidget(text_panel, 1)
        root.addWidget(self.header_group)

        controls_row: QHBoxLayout = QHBoxLayout()
        controls_row.addWidget(QLabel(self.tr("Filtro rápido:")))
        self.filter_edit: QLineEdit = QLineEdit()
        self.filter_edit.setPlaceholderText(self.tr("Filtrar por nome, patente ou status"))
        self.filter_edit.setToolTip(self.tr("Atalho: Ctrl+F para focar o filtro"))
        self.filter_edit.textChanged.connect(self._apply_filter)
        controls_row.addWidget(self.filter_edit, 1)

        self.high_contrast_toggle: QCheckBox = QCheckBox(self.tr("Alto contraste"))
        self.high_contrast_toggle.toggled.connect(self._toggle_high_contrast)
        controls_row.addWidget(self.high_contrast_toggle)

        root.addLayout(controls_row)

        self.state_label: QLabel = QLabel(self.tr("Pronto para carregar dados do esquadrão."))
        self.state_label.setStyleSheet(DSStyles.STATE_INFO)
        root.addWidget(self.state_label)

        # Tabela de pessoal
        self.table: QTableWidget = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Nome", "Patente", "Abates", "Missões", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setColumnWidth(1, self.RANK_MAX_W + 10)
        self.table.verticalHeader().setDefaultSectionSize(self.RANK_MAX_H + 8)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setToolTip(self.tr("Use setas para navegar entre os pilotos."))
        root.addWidget(self.table)

    # -------- Auxiliares de caminho --------
    @staticmethod
    def _assets_root() -> Path:
        return Path(__file__).resolve().parents[1] / "assets"

    @classmethod
    def _squadrons_root(cls) -> Path:
        return cls._assets_root() / "squadrons"

    @staticmethod
    def _norm(s: str) -> str:
        return (s or "").strip().lower()

    # -------- País p/ imagens de patentes --------
    def set_country(self, country_code: str) -> None:
        self._country_folder = (country_code or "GERMANY").strip().lower()

    # -------- Carregamento do meta e renderização --------
    def _candidate_meta_paths(self, squad_name: str) -> List[Path]:
        meta_dir: Path = self._squadrons_root() / "meta"
        if not meta_dir.exists():
            return []
        base: str = squad_name.strip()
        if not base:
            return []

        variants: Set[str] = {
            base,
            base.replace(" ", "-"),
            base.replace(" ", "_"),
            base.replace(" ", ""),
        }

        cands: List[Path] = []
        for v in variants:
            p: Path = meta_dir / f"{v}.json"
            if p.exists():
                cands.append(p)
        if cands:
            return cands

        for p in meta_dir.glob("*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data: Dict[str, Any] = json.load(f)
                name_in: str = (
                    data.get("squadronName")
                    or (data.get("squadronInfo") or {}).get("name")
                    or data.get("name")
                    or data.get("displayName")
                    or ""
                )
                if self._norm(name_in) == self._norm(base):
                    cands.append(p)
            except (OSError, json.JSONDecodeError):
                # Ignora arquivos que não podem ser lidos ou parseados
                continue
        return cands

    def _resolve_emblem_path(self, meta: Dict[str, Any]) -> Optional[Path]:
        raw: str = str(
            meta.get("emblemImage")
            or (meta.get("media") or {}).get("emblemImagePath")
            or ""
        ).strip()
        if raw:
            p: Path = Path(raw)
            if p.is_absolute() and p.exists():
                return p

            if raw.lower().startswith("squadrons/"):
                cand: Path = self._assets_root() / raw
                if cand.exists():
                    return cand

            if raw.lower().startswith("images/"):
                cand: Path = self._squadrons_root() / raw
                if cand.exists():
                    return cand

            images_dir: Path = self._squadrons_root() / "images"
            cand: Path = images_dir / raw
            if cand.exists():
                return cand

        fname_base: str = (
            meta.get("squadronName")
            or (meta.get("squadronInfo") or {}).get("name")
            or self._current_squad_name
            or ""
        )
        fname_base = fname_base.strip()
        if fname_base:
            images_dir: Path = self._squadrons_root() / "images"
            for ext in (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"):
                for v in {
                    fname_base,
                    fname_base.replace(" ", "-"),
                    fname_base.replace(" ", "_"),
                    fname_base.replace(" ", ""),
                }:
                    cand: Path = images_dir / f"{v}{ext}"
                    if cand.exists():
                        return cand

        return None

    def _render_details_html(self, meta: Dict[str, Any]) -> str:
        parts: List[str] = []

        # Cabeçalho reduzido: apenas Alias (sem ID e País)
        alias: str = meta.get("squadronAlias") or ""
        if alias:
            parts.append(f"<p><b>Alias:</b> {_esc(alias)}</p>")

        # História
        h: Union[str, Dict[str, Any], None] = meta.get("history")
        if isinstance(h, str) and h.strip():
            parts.append(f"<h3>História</h3><p>{_esc(h)}</p>")
        elif isinstance(h, dict):
            summary: str = _esc(h.get("summary", ""))
            if summary:
                parts.append(f"<h3>História</h3><p>{summary}</p>")
            formation: Dict[str, Any] = h.get("formation") or {}
            if any(formation.get(k) for k in ("date", "location", "context", "firstCommander")):
                parts.append("<h3>Formação</h3><ul>")
                if formation.get("date"):
                    parts.append(f"<li><b>Data:</b> {_esc(formation.get('date'))}</li>")
                if formation.get("location"):
                    parts.append(f"<li><b>Local:</b> {_esc(formation.get('location'))}</li>")
                if formation.get("firstCommander"):
                    parts.append(f"<li><b>Primeiro comandante:</b> {_esc(formation.get('firstCommander'))}</li>")
                if formation.get("context"):
                    parts.append(f"<li><b>Contexto:</b> {_esc(formation.get('context'))}</li>")
                parts.append("</ul>")
            if isinstance(h.get("designations"), list) and h["designations"]:
                parts.append("<h3>Designações</h3><ul>")
                for d in h["designations"]:
                    nm: str = _esc((d or {}).get("name", ""))
                    pr: str = _esc((d or {}).get("period", ""))
                    if nm or pr:
                        parts.append(f"<li>{nm} {('— ' + pr) if pr else ''}</li>")
                parts.append("</ul>")
            if isinstance(h.get("notableEvents"), list) and h["notableEvents"]:
                parts.append("<h3>Eventos notáveis</h3><ul>")
                for e in h["notableEvents"]:
                    dt: str = _esc((e or {}).get("date", ""))
                    ev: str = _esc((e or {}).get("event", "") or (e or {}).get("description", ""))
                    if dt or ev:
                        parts.append(f"<li>{dt} — {ev}</li>")
                parts.append("</ul>")
            if isinstance(h.get("commanders"), list) and h["commanders"]:
                parts.append("<h3>Comandantes</h3><ul>")
                for c in h["commanders"]:
                    nm: str = _esc((c or {}).get("name", ""))
                    tn: str = _esc((c or {}).get("tenure", ""))
                    ft: str = _esc((c or {}).get("fate", ""))
                    line: str = nm
                    if tn:
                        line += f" — {tn}"
                    if ft:
                        line += f" ({ft})"
                    if line.strip():
                        parts.append(f"<li>{line}</li>")
                parts.append("</ul>")
            if isinstance(h.get("notablePilots"), list) and h["notablePilots"]:
                parts.append("<h3>Pilotos notáveis</h3><ul>")
                for p in h["notablePilots"]:
                    parts.append(f"<li>{_esc(p)}</li>")
                parts.append("</ul>")
            if isinstance(h.get("aircraftUsed"), list) and h["aircraftUsed"]:
                parts.append("<h3>Aeronaves</h3><ul>")
                for a in h["aircraftUsed"]:
                    parts.append(f"<li>{_esc(a)}</li>")
                parts.append("</ul>")

        # Equipment (estrutura Esc-15)
        eq: Dict[str, Any] = meta.get("equipment") or {}
        if isinstance(eq.get("aircraftUsed"), list) and eq["aircraftUsed"]:
            parts.append("<h3>Aeronaves</h3><ul>")
            for a in eq["aircraftUsed"]:
                parts.append(f"<li>{_esc(a)}</li>")
            parts.append("</ul>")
        mk: Dict[str, Any] = eq.get("markings") or meta.get("markings") or {}
        if mk:
            desc: str = _esc(mk.get("description", ""))
            if desc:
                parts.append(f"<h3>Marcações</h3><p>{desc}</p>")
            ins: str = _esc(mk.get("insignia", ""))
            ins_id: str = _esc(mk.get("insigniaId", ""))
            if ins or ins_id:
                parts.append("<ul>")
                if ins:
                    parts.append(f"<li><b>Insígnia:</b> {ins}</li>")
                if ins_id:
                    parts.append(f"<li><b>ID:</b> {ins_id}</li>")
                parts.append("</ul>")

        # Estatísticas
        st: Dict[str, Any] = meta.get("statistics") or {}
        if st:
            parts.append("<h3>Estatísticas</h3><ul>")
            if "totalVictories" in st:
                parts.append(f"<li><b>Vitórias:</b> {_esc(st.get('totalVictories'))}</li>")
            if "aces" in st:
                parts.append(f"<li><b>Ases:</b> {_esc(st.get('aces'))}</li>")
            vb: Any = st.get("victoryBreakdown") or {}
            if vb:
                parts.append(f"<li><b>Detalhe de vitórias:</b> {_esc(vb)}</li>")
            cs: Any = st.get("casualties") or {}
            if cs:
                parts.append(f"<li><b>Baixas:</b> {_esc(cs)}</li>")
            if "citations" in st:
                parts.append(f"<li><b>Citações:</b> {_esc(st.get('citations'))}</li>")
            parts.append("</ul>")

        # Aeródromos
        af_list: List[Dict[str, str]] = []
        if isinstance(meta.get("airfields"), list) and meta["airfields"]:
            for it in meta["airfields"]:
                af_list.append({
                    "start": (it or {}).get("start", ""),
                    "end": (it or {}).get("end", ""),
                    "airfield": (it or {}).get("airfield", ""),
                })
        if isinstance(meta.get("deploymentHistory"), list) and meta["deploymentHistory"]:
            for it in meta["deploymentHistory"]:
                af_list.append({
                    "start": (it or {}).get("startDate", ""),
                    "end": (it or {}).get("endDate", ""),
                    "airfield": (it or {}).get("airfieldId", ""),
                })
        if af_list:
            parts.append("<h3>Aeródromos</h3><ul>")
            for it in af_list:
                line: str = f"{_esc(it.get('start'))} → {_esc(it.get('end'))}: {_esc(it.get('airfield'))}"
                parts.append(f"<li>{line}</li>")
            parts.append("</ul>")

        # Observação: seção "Fonte" removida conforme solicitado.

        return "".join(parts)

    def set_squad_overview(self, squad_name: str) -> None:
        """Carrega emblema e dados completos do esquadrão a partir de assets/squadrons/meta."""
        self._current_squad_name = squad_name or ""

        self.title_label.setText(self._current_squad_name or "N/A")
        self.details_label.setText("")
        self.emblem_label.setPixmap(QPixmap())
        self.emblem_label.setText(self.tr("Sem emblema"))
        self.emblem_label.setStyleSheet(DSStyles.PANEL_PLACEHOLDER)

        if not self._current_squad_name:
            self._set_view_state(DSStates.EMPTY, self.tr("Nenhum esquadrão selecionado."))
            return

        cands: List[Path] = self._candidate_meta_paths(self._current_squad_name)
        if not cands:
            self._set_view_state(DSStates.EMPTY, self.tr("Metadados do esquadrão não encontrados."))
            return

        meta_path: Path = cands[0]
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta: Dict[str, Any] = json.load(f)
        except (OSError, json.JSONDecodeError):
            logger.warning(f"Falha ao ler ou parsear o arquivo de metadados do esquadrão: {meta_path}")
            self._set_view_state(DSStates.ERROR, self.tr("Falha ao ler metadados do esquadrão."))
            return

        title: str = (
            meta.get("squadronName")
            or (meta.get("squadronInfo") or {}).get("name")
            or self._current_squad_name
        )
        self.title_label.setText(title if title else "N/A")

        emb: Optional[Path] = self._resolve_emblem_path(meta)
        if emb and emb.exists():
            pm: QPixmap = QPixmap(str(emb))
            if not pm.isNull():
                scaled: QPixmap = pm.scaled(self.EMBLEM_W, self.EMBLEM_H, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.emblem_label.setStyleSheet("")
                self.emblem_label.setText("")
                self.emblem_label.setPixmap(scaled)

        self.details_label.setText(self._render_details_html(meta))
        self._set_view_state(DSStates.SUCCESS, self.tr("Dados do esquadrão carregados."))

    # -------- Ícone de patente --------
    @staticmethod
    def _ranks_base_dir() -> Path:
        return Path(__file__).resolve().parents[1] / "assets" / "ranks"

    def _rank_pixmap(self, rank_name: str) -> Optional[QPixmap]:
        key: str = self._norm(rank_name).replace(" ", "_").replace("-", "_")
        if not key:
            return None
        base: Path = self._ranks_base_dir() / (self._country_folder or "germany")
        if not base.exists():
            return None
        for ext in (".png", ".PNG", ".jpg", ".jpeg", ".JPG", ".JPEG"):
            p: Path = base / f"{key}{ext}"
            pm: QPixmap = QPixmap(str(p))
            if not pm.isNull():
                return pm
        return None

    def _should_rotate_horizontal(self, rank_name: str) -> bool:
        if self._country_folder not in ("germany", "ger", "de", "deu"):
            return False
        key: str = self._norm(rank_name)
        return key in {"kommandeur", "kommander", "oberleutnant", "leutnant"}

    # -------- Ordenação por posto --------
    def _rank_weight(self, rank_name: str) -> int:
        table: List[str] = self.RANK_ORDER.get(self._country_folder, [])
        key: str = self._norm(rank_name).replace(" ", "_").replace("-", "_")
        try:
            return table.index(key)
        except ValueError:
            heuristics: List[str] = [
                "kommand", "major", "hauptmann", "captain", "lieutenant",
                "leutnant", "adjudant", "sergent", "sergeant", "corporal"
            ]
            for i, h in enumerate(heuristics):
                if h in key:
                    return len(table) + i
            return len(table) + len(heuristics) + 100

    def _set_view_state(self, state: str, message: str) -> None:
        self.state_label.setText(message)
        if state == DSStates.SUCCESS:
            self.state_label.setStyleSheet(DSStyles.STATE_SUCCESS)
        elif state == DSStates.ERROR:
            self.state_label.setStyleSheet(DSStyles.STATE_ERROR)
        elif state == DSStates.EMPTY:
            self.state_label.setStyleSheet(DSStyles.STATE_WARNING)
        else:
            self.state_label.setStyleSheet(DSStyles.STATE_INFO)

    def keyPressEvent(self, event) -> None:
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_F:
            self.filter_edit.setFocus()
            self.filter_edit.selectAll()
            return
        super().keyPressEvent(event)

    def _apply_filter(self, text: str) -> None:
        rows: List[Dict[str, str]] = []
        for row in range(self.table.rowCount()):
            rank_widget = self.table.cellWidget(row, 1)
            rows.append(
                {
                    "name": (self.table.item(row, 0).text() if self.table.item(row, 0) else ""),
                    "rank": str(getattr(rank_widget, "rank_name", "") if rank_widget else ""),
                    "victories": (self.table.item(row, 2).text() if self.table.item(row, 2) else ""),
                    "missions": (self.table.item(row, 3).text() if self.table.item(row, 3) else ""),
                    "status": (self.table.item(row, 4).text() if self.table.item(row, 4) else ""),
                }
            )

        visibility = self._vm.filter_visibility(rows, text)
        for row, is_visible in enumerate(visibility):
            self.table.setRowHidden(row, not is_visible)

        visible_rows = sum(1 for v in visibility if v)
        filter_state = self._vm.state_for_visible_count(visible_rows)
        self._set_view_state(filter_state.state, self.tr(filter_state.message))

    def _toggle_high_contrast(self, enabled: bool) -> None:
        if enabled:
            self.table.setStyleSheet(
                "QTableWidget { background:#111; color:#fff; gridline-color:#777; }"
                "QHeaderView::section { background:#222; color:#fff; font-weight:bold; }"
            )
            self.header_group.setStyleSheet("QGroupBox { color:#fff; }")
        else:
            self.table.setStyleSheet("")
            self.header_group.setStyleSheet("")

    # -------- Preenchimento da tabela --------
    def set_squadron(self, members: List[Dict[str, Any]]) -> None:
        members = members or []
        member_state = self._vm.state_for_members(members)
        if member_state.state == DSStates.EMPTY:
            self.table.setRowCount(0)
            self._set_view_state(member_state.state, self.tr(member_state.message))
            return
        sorted_members: List[Dict[str, Any]] = sorted(
            members,
            key=lambda m: (self._rank_weight(m.get("rank", "")), (m.get("name", "") or "").lower())
        )

        self.table.setRowCount(len(sorted_members))

        for r, m in enumerate(sorted_members):
            name_item = QTableWidgetItem(m.get('name', ''))
            name_item.setToolTip(name_item.text())
            self.table.setItem(r, 0, name_item)

            rank_name: str = m.get('rank', '') or ''
            lbl: RankIconLabel = RankIconLabel(rank_name, delay_ms=2000, parent=self.table)
            lbl.setAlignment(Qt.AlignCenter)

            pm: Optional[QPixmap] = self._rank_pixmap(rank_name)
            if pm is not None:
                rotate: bool = self._should_rotate_horizontal(rank_name) and (pm.height() > pm.width())
                if rotate:
                    pm = pm.transformed(QTransform().rotate(90), Qt.SmoothTransformation)

                col_w: int = max(80, self.table.columnWidth(1) - 10)
                max_w: int = min(self.RANK_MAX_W, col_w)
                max_h: int = self.RANK_MAX_H
                scaled: QPixmap = pm.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                lbl.setPixmap(scaled)
                self.table.setRowHeight(r, max(self.table.rowHeight(r), scaled.height() + 6))
            else:
                lbl.setText("—")
                lbl.setStyleSheet("color:#888;")

            self.table.setCellWidget(r, 1, lbl)
            victories_item = QTableWidgetItem(str(m.get('victories', 0)))
            victories_item.setToolTip(victories_item.text())
            self.table.setItem(r, 2, victories_item)
            missions_item = QTableWidgetItem(str(m.get('missions_flown', 0)))
            missions_item.setToolTip(missions_item.text())
            self.table.setItem(r, 3, missions_item)

            status_text: str = m.get('status', '') or ''
            status_item: QTableWidgetItem = QTableWidgetItem(status_text)
            status_item.setToolTip(status_text)
            norm: str = (status_text or '').strip().lower()
            color: Optional[QColor] = self.STATUS_COLORS.get(norm)
            if color:
                status_item.setForeground(color)
                f: QFont = status_item.font()
                if norm in ('kia', 'morto', 'mia', 'desaparecido', 'wounded', 'ferido', 'pow', 'prisioneiro'):
                    f.setBold(True)
                status_item.setFont(f)
            self.table.setItem(r, 4, status_item)