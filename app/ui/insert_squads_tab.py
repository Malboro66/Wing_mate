# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - app/ui/insert_squads_tab.py
# Aba temporária "Insert Squads" para enriquecer dados de esquadrões
# ===================================================================

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.application.squadron_enrichment_application_service import (
    SquadronEnrichmentApplicationService,
)
from app.core.squadron_enrichment_service import SquadronEnrichmentService
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class InsertSquadsTab(QWidget):
    def __init__(
        self,
        app_service: Optional[SquadronEnrichmentApplicationService] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        if app_service is None:
            domain_service: SquadronEnrichmentService = SquadronEnrichmentService()
            self._app_service: SquadronEnrichmentApplicationService = (
                SquadronEnrichmentApplicationService(domain_service)
            )
        else:
            self._app_service = app_service
        self._pwcgfc_path: Optional[Path] = None
        self._squadron_dir: Optional[Path] = None
        self._selected_json_path: Optional[Path] = None
        self._selected_emblem_src: Optional[Path] = None

        # Destino dentro de assets
        self._assets_root: Path = Path(__file__).resolve().parents[1] / "assets"
        self._assets_emblems_dir: Path = self._assets_root / "squadrons" / "images"
        self._assets_meta_dir: Path = self._assets_root / "squadrons" / "meta"

        self._build_ui()

    # ---------------- UI ----------------
    def _build_ui(self) -> None:
        outer: QVBoxLayout = QVBoxLayout(self)

        sel_group: QGroupBox = QGroupBox(self.tr("Seleção de Esquadrão"))
        sel_form: QFormLayout = QFormLayout(sel_group)

        self.squad_combo: QComboBox = QComboBox()
        self.squad_combo.currentIndexChanged.connect(self._on_squad_changed)
        sel_form.addRow(self.tr("Esquadrão (PWCG):"), self.squad_combo)

        self.country_label: QLabel = QLabel("N/A")
        sel_form.addRow(self.tr("País:"), self.country_label)

        outer.addWidget(sel_group)

        af_group: QGroupBox = QGroupBox(self.tr("Aeródromos por data"))
        af_v: QVBoxLayout = QVBoxLayout(af_group)

        self.af_table: QTableWidget = QTableWidget(0, 3)
        self.af_table.setHorizontalHeaderLabels(
            [self.tr("Início"), self.tr("Fim"), self.tr("Aeródromo")]
        )
        self.af_table.horizontalHeader().setStretchLastSection(True)
        af_v.addWidget(self.af_table)

        outer.addWidget(af_group)

        edit_group: QGroupBox = QGroupBox(self.tr("Dados Enriquecidos"))
        edit_form: QFormLayout = QFormLayout(edit_group)

        emblem_row: QHBoxLayout = QHBoxLayout()
        self.emblem_preview: QLabel = QLabel(self.tr("Sem emblema"))
        self.emblem_preview.setAlignment(Qt.AlignCenter)
        self.emblem_preview.setFixedSize(160, 160)
        self.emblem_preview.setStyleSheet(
            "color:#888; border:1px solid #444; background:#1e1e1e;"
        )
        emblem_btn: QPushButton = QPushButton(self.tr("Selecionar Emblema (.png/.jpg)"))
        emblem_btn.clicked.connect(self._choose_emblem)
        emblem_row.addWidget(self.emblem_preview)
        emblem_row.addWidget(emblem_btn)

        emblem_holder: QWidget = QWidget()
        emblem_holder.setLayout(emblem_row)
        edit_form.addRow(self.tr("Símbolo do Esquadrão:"), emblem_holder)

        self.history_edit: QTextEdit = QTextEdit()
        self.history_edit.setPlaceholderText(
            self.tr("Informações históricas do esquadrão...")
        )
        self.history_edit.setFixedHeight(150)
        edit_form.addRow(self.tr("Histórico:"), self.history_edit)

        outer.addWidget(edit_group)

        bottom: QHBoxLayout = QHBoxLayout()
        bottom.addStretch(1)
        self.btn_save: QPushButton = QPushButton(self.tr("Salvar"))
        self.btn_save.clicked.connect(self._save_enriched_data)
        self.btn_save.setEnabled(False)
        bottom.addWidget(self.btn_save)
        outer.addLayout(bottom)

    # ---------------- Integração ----------------
    def set_pwcgfc_path(self, pwcgfc_path: str) -> None:
        self._pwcgfc_path = Path(pwcgfc_path) if pwcgfc_path else None
        self._squadron_dir = None
        self._selected_json_path = None
        self._selected_emblem_src = None

        self.country_label.setText("N/A")
        self._clear_airfields()
        self._clear_emblem_preview()
        self.history_edit.clear()
        self.btn_save.setEnabled(False)

        if not self._pwcgfc_path:
            return

        sq_dir: Path = self._pwcgfc_path / "FCData" / "Input" / "Squadron"
        if not sq_dir.exists():
            QMessageBox.warning(
                self,
                self.tr("PWCG"),
                self.tr("Pasta de esquadrões não encontrada:\n") + str(sq_dir),
            )
            return
        self._squadron_dir = sq_dir

        try:
            self._assets_emblems_dir.mkdir(parents=True, exist_ok=True)
            self._assets_meta_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(
                self,
                self.tr("Erro de Diretório"),
                self.tr("Não foi possível criar os diretórios de assets:\n") + str(e),
            )
            return

        self._refresh_squad_list()

    def _refresh_squad_list(self) -> None:
        if not self._squadron_dir:
            return

        try:
            all_jsons: List[Path] = sorted(
                self._squadron_dir.glob("*.json"), key=lambda p: p.name.lower()
            )
        except OSError as e:
            QMessageBox.warning(
                self,
                self.tr("Erro de Leitura"),
                self.tr("Não foi possível listar os arquivos de esquadrões:\n") + str(e),
            )
            return

        remaining: List[Path] = []
        for p in all_jsons:
            sq_id: str = p.stem
            meta_path: Path = self._assets_meta_dir / f"{sq_id}.json"
            if not meta_path.exists():
                remaining.append(p)

        self.squad_combo.blockSignals(True)
        self.squad_combo.clear()
        for p in remaining:
            self.squad_combo.addItem(p.stem, str(p))
        self.squad_combo.blockSignals(False)

        if remaining:
            self.squad_combo.setCurrentIndex(0)
            self._on_squad_changed(0)
        else:
            self._selected_json_path = None
            self.country_label.setText("N/A")
            self._clear_airfields()
            self._clear_emblem_preview()
            self.history_edit.clear()
            self.btn_save.setEnabled(False)

    # ---------------- Eventos ----------------
    def _on_squad_changed(self, index: int) -> None:
        self._selected_emblem_src = None
        self._clear_emblem_preview()
        self.history_edit.clear()
        self.btn_save.setEnabled(False)
        self._clear_airfields()
        self.country_label.setText("N/A")

        path_str: Optional[str] = self.squad_combo.itemData(index)
        self._selected_json_path = Path(path_str) if path_str else None
        if not self._selected_json_path or not self._selected_json_path.exists():
            return

        try:
            country, airfields = self._app_service.load_preview(self._selected_json_path)
        except (UnicodeDecodeError, OSError, ValueError) as e:
            QMessageBox.warning(
                self,
                self.tr("Erro de Leitura"),
                self.tr("Não foi possível ler o arquivo JSON:\n")
                + str(self._selected_json_path)
                + "\n"
                + str(e),
            )
            return

        self.country_label.setText(country or "N/A")
        self._fill_airfields_table(airfields)

        self.btn_save.setEnabled(True)

    def _choose_emblem(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Selecionar Emblema"),
            "",
            self.tr("Imagens (*.png *.jpg *.jpeg)"),
        )
        if not path:
            return

        src: Path = Path(path)
        pm: QPixmap = QPixmap(str(src))
        if pm.isNull():
            QMessageBox.warning(
                self,
                self.tr("Emblema"),
                self.tr("Não foi possível carregar a imagem selecionada."),
            )
            return

        scaled: QPixmap = pm.scaled(
            self.emblem_preview.width(),
            self.emblem_preview.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.emblem_preview.setStyleSheet("")
        self.emblem_preview.setText("")
        self.emblem_preview.setPixmap(scaled)
        self._selected_emblem_src = src

    # ---------------- Persistência ----------------
    def _save_enriched_data(self) -> None:
        if not self._selected_json_path:
            QMessageBox.warning(
                self, self.tr("Salvar"), self.tr("Selecione um esquadrão.")
            )
            return

        emblem_rel: str = ""
        if self._selected_emblem_src and self._selected_emblem_src.exists():
            ext: str = self._selected_emblem_src.suffix.lower()
            if ext not in (".png", ".jpg", ".jpeg"):
                ext = ".png"
            emblem_dst: Path = self._assets_emblems_dir / f"{sq_id}{ext}"
            try:
                self._assets_emblems_dir.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(str(self._selected_emblem_src), str(emblem_dst))
                emblem_rel = str(Path("squadrons") / "images" / emblem_dst.name)
            except (OSError, shutil.Error) as e:
                QMessageBox.critical(
                    self, self.tr("Emblema"), self.tr("Falha ao copiar emblema:\n") + str(e)
                )
                return

        sq_id, enriched = self._app_service.build_payload(
            source_path=self._selected_json_path,
            history=self.history_edit.toPlainText(),
            emblem_rel=emblem_rel,
        )

        out_path: Path = self._assets_meta_dir / f"{sq_id}.json"
        try:
            self._app_service.persist_payload(out_path, enriched)
        except (OSError, TypeError, ValueError) as e:
            QMessageBox.critical(
                self, self.tr("Salvar"), self.tr("Falha ao salvar JSON:\n") + str(e)
            )
            return

        QMessageBox.information(
            self, self.tr("Salvar"), self.tr("Arquivo criado:\n") + str(out_path)
        )

        self._refresh_squad_list()

    # ---------------- Utilidades ----------------
    def _fill_airfields_table(self, items: List[Dict[str, str]]) -> None:
        self.af_table.setRowCount(len(items))
        for i, it in enumerate(items):
            self.af_table.setItem(i, 0, QTableWidgetItem(it.get("start", "")))
            self.af_table.setItem(i, 1, QTableWidgetItem(it.get("end", "")))
            self.af_table.setItem(i, 2, QTableWidgetItem(it.get("airfield", "")))

    def _clear_airfields(self) -> None:
        self.af_table.setRowCount(0)

    def _clear_emblem_preview(self) -> None:
        self.emblem_preview.setPixmap(QPixmap())
        self.emblem_preview.setText(self.tr("Sem emblema"))
        self.emblem_preview.setStyleSheet(
            "color:#888; border:1px solid #444; background:#1e1e1e;"
        )
