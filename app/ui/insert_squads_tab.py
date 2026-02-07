# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - app/ui/insert_squads_tab.py
# Aba temporária "Insert Squads" para enriquecer dados de esquadrões
# ===================================================================

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QFormLayout
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget


class InsertSquadsTab(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
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

        # Seleção de esquadrão
        sel_group: QGroupBox = QGroupBox(self.tr("Seleção de Esquadrão"))
        sel_form: QFormLayout = QFormLayout(sel_group)

        self.squad_combo: QComboBox = QComboBox()
        self.squad_combo.currentIndexChanged.connect(self._on_squad_changed)
        sel_form.addRow(self.tr("Esquadrão (PWCG):"), self.squad_combo)

        self.country_label: QLabel = QLabel("N/A")
        sel_form.addRow(self.tr("País:"), self.country_label)

        outer.addWidget(sel_group)

        # Tabela de aeródromos
        af_group: QGroupBox = QGroupBox(self.tr("Aeródromos por data"))
        af_v: QVBoxLayout = QVBoxLayout(af_group)

        self.af_table: QTableWidget = QTableWidget(0, 3)
        self.af_table.setHorizontalHeaderLabels(
            [self.tr("Início"), self.tr("Fim"), self.tr("Aeródromo")]
        )
        self.af_table.horizontalHeader().setStretchLastSection(True)
        af_v.addWidget(self.af_table)

        outer.addWidget(af_group)

        # Emblema + histórico
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

        # Rodapé
        bottom: QHBoxLayout = QHBoxLayout()
        bottom.addStretch(1)
        self.btn_save: QPushButton = QPushButton(self.tr("Salvar"))
        self.btn_save.clicked.connect(self._save_enriched_data)
        self.btn_save.setEnabled(False)
        bottom.addWidget(self.btn_save)
        outer.addLayout(bottom)

    # ---------------- Integração ----------------
    def set_pwcgfc_path(self, pwcgfc_path: str) -> None:
        """
        Inicializa a aba com a pasta do PWCGFC.
        Independe de sincronização de campanha.
        """
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

        # Garante pastas de saída
        try:
            self._assets_emblems_dir.mkdir(parents=True, exist_ok=True)
            self._assets_meta_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(
                self,
                self.tr("Erro de Diretório"),
                self.tr("Não foi possível criar os diretórios de assets:\n") + str(e)
            )
            return

        self._refresh_squad_list()

    def _refresh_squad_list(self) -> None:
        """Recarrega a combo removendo os que já têm meta/<id>.json."""
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
                self.tr("Não foi possível listar os arquivos de esquadrões:\n") + str(e)
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

        data: Dict[str, Any] = self._read_json(self._selected_json_path)
        _name, country, airfields = self._extract_fields(data)
        self.country_label.setText(country or "N/A")
        self._fill_airfields_table(airfields)

        self.btn_save.setEnabled(True)

    def _choose_emblem(self) -> None:
        path: str
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

        base_in: Dict[str, Any] = self._read_json(self._selected_json_path)
        sq_id, sq_name = self._resolve_id_and_name(base_in, self._selected_json_path)

        # Copia emblema (opcional)
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

        # Campos do JSON original
        _name, country, airfields = self._extract_fields(base_in)

        enriched: Dict[str, Any] = {
            "squadronId": sq_id,
            "squadronName": sq_name,
            "country": country or "",
            "history": self.history_edit.toPlainText().strip(),
            "emblemImage": emblem_rel,  # relativo a assets/
            "airfields": airfields,
            "source": {"pwcg_squadron_file": str(self._selected_json_path)},
        }

        out_path: Path = self._assets_meta_dir / f"{sq_id}.json"
        try:
            self._assets_meta_dir.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(enriched, f, ensure_ascii=False, indent=2)
        except (OSError, json.JSONEncodeError) as e:
            QMessageBox.critical(
                self, self.tr("Salvar"), self.tr("Falha ao salvar JSON:\n") + str(e)
            )
            return

        QMessageBox.information(
            self, self.tr("Salvar"), self.tr("Arquivo criado:\n") + str(out_path)
        )

        # Após salvar, recarrega a lista excluindo os já populados
        self._refresh_squad_list()

    # ---------------- Utilidades ----------------
    def _read_json(self, path: Path) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (UnicodeDecodeError, json.JSONDecodeError):
            # Tenta com latin-1 se falhar com utf-8
            try:
                with open(path, "r", encoding="latin-1") as f:
                    return json.load(f)
            except (UnicodeDecodeError, json.JSONDecodeError, OSError) as e:
                QMessageBox.warning(
                    self,
                    self.tr("Erro de Leitura"),
                    self.tr("Não foi possível ler o arquivo JSON:\n") + str(path) + "\n" + str(e)
                )
                return {}
        except OSError as e:
            QMessageBox.warning(
                self,
                self.tr("Erro de Leitura"),
                self.tr("Não foi possível acessar o arquivo:\n") + str(path) + "\n" + str(e)
            )
            return {}

    @staticmethod
    def _resolve_id_and_name(data: Dict[str, Any], p: Path) -> Tuple[str, str]:
        sq_id: str = p.stem
        for k in ("squadronName", "name", "displayName", "id", "squadron_id"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                return sq_id, v.strip()
        return sq_id, sq_id

    @staticmethod
    def _extract_fields(data: Dict[str, Any]) -> Tuple[str, str, List[Dict[str, str]]]:
        """
        Retorna: (name, country, airfields[])
        airfields: lista de objetos {start, end, airfield}
        Suporta:
          - airfields como dict {"YYYYMMDD": "Base"} (formato PWCG comum)
          - airfields como list de dicts
          - airfieldHistory como list de dicts
          - bases como list de dicts
        """
        # Nome
        name: str = ""
        for k in ("squadronName", "name", "displayName", "id", "squadron_id"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                name = v.strip()
                break

        # País
        country: str = ""
        for k in ("country", "nation", "countryCode"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                country = v.strip()
                break

        airfields: List[Dict[str, str]] = []

        def add_af(s: Any, e: Any, a: Any) -> None:
            start: str = str(s or "").strip()
            end: str = str(e or "").strip()
            af: str = str(a or "").strip()
            if af:
                airfields.append({"start": start, "end": end, "airfield": af})

        # 1) airfields como dict {"YYYYMMDD": "Nome"}
        af_dict = data.get("airfields")
        if isinstance(af_dict, dict):
            items: List[Tuple[str, str]] = sorted(((str(k), str(v)) for k, v in af_dict.items()), key=lambda x: x[0])
            for i, (start, af_name) in enumerate(items):
                end = items[i + 1][0] if i + 1 < len(items) else ""
                add_af(start, end, af_name)

        # 2) airfields como lista de dicts
        if isinstance(data.get("airfields"), list):
            for it in data["airfields"]:
                if isinstance(it, dict):
                    add_af(
                        it.get("start"),
                        it.get("end"),
                        it.get("airfield") or it.get("base") or it.get("name"),
                    )

        # 3) Histórico em airfieldHistory
        if isinstance(data.get("airfieldHistory"), list):
            for it in data["airfieldHistory"]:
                if isinstance(it, dict):
                    add_af(it.get("from"), it.get("to"), it.get("airfield") or it.get("name"))

        # 4) Estruturas alternativas bases
        if not airfields and isinstance(data.get("bases"), list):
            for it in data["bases"]:
                if isinstance(it, dict):
                    add_af(
                        it.get("startDate"),
                        it.get("endDate"),
                        it.get("airfield") or it.get("base"),
                    )

        return name, country, airfields

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