# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - app/ui/input_medals_tab.py
# Cadastro/Edição de medalhas com ribbon + descrição separada + modelos de condições do PWCG
# Emite sinais para recarregar a aba Medalhas
# ===================================================================

import json
import shutil
import logging
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QFileDialog, QLabel, QGroupBox, QFormLayout,
    QLineEdit, QTextEdit, QMessageBox, QCheckBox, QComboBox
)

logger = logging.getLogger(__name__)


@contextmanager
def atomic_json_write(filepath: Path):
    """Context manager para escrita atômica de arquivos JSON.
    
    Grava em arquivo temporário e realiza rename atômico apenas em caso de sucesso.
    Em caso de falha, o arquivo original permanece intocado.
    
    Args:
        filepath: Caminho do arquivo JSON de destino
        
    Yields:
        File handle para escrita
        
    Raises:
        OSError: Se houver falha na escrita ou renomeação do arquivo
    """
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=filepath.parent,
        prefix='.tmp_',
        suffix='.json'
    )
    tmp_file = Path(tmp_path)
    
    try:
        with open(tmp_fd, 'w', encoding='utf-8') as f:
            yield f
        tmp_file.replace(filepath)  # Operação atômica no sistema de arquivos
        logger.info(f"Arquivo {filepath.name} gravado com sucesso (atômico)")
    except Exception as e:
        logger.error(f"Falha na escrita atômica de {filepath}: {e}")
        if tmp_file.exists():
            tmp_file.unlink()
        raise
    finally:
        try:
            os.close(tmp_fd)
        except OSError:
            pass


class PathResolver:
    """Utilitário para resolução de caminhos de assets (absolutos ou relativos)."""
    
    @staticmethod
    def resolve_asset_path(base_path: Path, relative_or_absolute: str) -> Optional[Path]:
        """Resolve caminho de asset, suportando caminhos absolutos e relativos.
        
        Args:
            base_path: Diretório base para resolução de caminhos relativos
            relative_or_absolute: String com caminho absoluto ou relativo
            
        Returns:
            Path do arquivo se existir, None caso contrário
        """
        if not relative_or_absolute:
            return None
        
        p = Path(relative_or_absolute)
        if p.is_absolute():
            return p if p.exists() else None
        
        candidate = base_path / relative_or_absolute
        return candidate if candidate.exists() else None


class InputMedalsTab(QWidget):
    """Aba para cadastro e edição de medalhas/condecorações.
    
    Permite adicionar novas medalhas com imagem, ribbon, descrição e condições.
    Suporta importação de condições de arquivos PWCG.
    
    Signals:
        medal_added: Emitido quando nova medalha é adicionada (dict com dados)
        medal_updated: Emitido quando medalha é editada (índice, dict com dados)
    """
    
    medal_added = pyqtSignal(dict)
    medal_updated = pyqtSignal(int, dict)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Inicializa a aba de cadastro de medalhas.
        
        Args:
            parent: Widget pai (opcional)
        """
        super().__init__(parent)
        
        # Configuração de diretórios
        self._assets_root: Path = Path(__file__).resolve().parents[1] / "assets" / "medals"
        self._assets_meta_dir: Path = self._assets_root / "meta"
        self._assets_images_dir: Path = self._assets_root / "images"
        self._assets_ribbons_dir: Path = self._assets_root / "ribbons"
        self._meta_file: Path = self._assets_meta_dir / "medals.json"
        
        # Estado interno
        self._pwcgfc_path: Optional[Path] = None
        self._pwcg_models: List[Dict[str, Any]] = []
        self.medals: List[Dict[str, Any]] = []
        self.selected_idx: Optional[int] = None
        
        # Construção da interface
        self._build_ui()
        self._ensure_dirs()
        self._load_medals()
        self._reload_pwcg_models()
    
    def _build_ui(self) -> None:
        """Constrói a interface gráfica da aba."""
        layout: QVBoxLayout = QVBoxLayout(self)
        
        # Tabela de medalhas
        self.table: QTableWidget = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Nome", "Imagem", "Ribbon", "Editar"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        
        # Botão de adicionar
        row_btns: QHBoxLayout = QHBoxLayout()
        row_btns.addStretch()
        self.btn_add: QPushButton = QPushButton("Adicionar Medalha/Condecoração")
        self.btn_add.clicked.connect(self._show_form_add)
        row_btns.addWidget(self.btn_add)
        layout.addLayout(row_btns)
        
        # Formulário de cadastro/edição
        self.form_group: QGroupBox = QGroupBox(self.tr("Cadastro/Edição de Medalha"))
        self.form_group.setVisible(False)
        form: QFormLayout = QFormLayout(self.form_group)
        
        # Campo: Nome
        self.nome_input: QLineEdit = QLineEdit()
        
        # Campo: Imagem
        self.img_path_input: QLineEdit = QLineEdit()
        self.img_path_input.setReadOnly(True)
        img_btn: QPushButton = QPushButton("Selecionar Imagem")
        img_btn.clicked.connect(self._select_img)
        img_box: QHBoxLayout = QHBoxLayout()
        img_box.addWidget(self.img_path_input)
        img_box.addWidget(img_btn)
        img_wrap: QWidget = QWidget()
        img_wrap.setLayout(img_box)
        
        # Campo: Ribbon
        self.ribbon_path_input: QLineEdit = QLineEdit()
        self.ribbon_path_input.setReadOnly(True)
        rib_btn: QPushButton = QPushButton("Selecionar Ribbon (opcional)")
        rib_btn.clicked.connect(self._select_ribbon)
        rib_box: QHBoxLayout = QHBoxLayout()
        rib_box.addWidget(self.ribbon_path_input)
        rib_box.addWidget(rib_btn)
        rib_wrap: QWidget = QWidget()
        rib_wrap.setLayout(rib_box)
        
        # Campo: Nação
        self.country_combo: QComboBox = QComboBox()
        self.country_combo.addItems(["germany", "france", "britain", "usa", "belgian"])
        
        # Campo: Descrição
        self.descricao_edit: QTextEdit = QTextEdit()
        self.descricao_edit.setPlaceholderText("Descrição histórica/explicativa da medalha")
        self.descricao_edit.setMinimumHeight(90)
        
        # Seção PWCG
        self.use_pwcg_chk: QCheckBox = QCheckBox("Usar condições do PWCG (se disponíveis)")
        self.use_pwcg_chk.stateChanged.connect(self._toggle_pwcg_models)
        self.pwcg_model_combo: QComboBox = QComboBox()
        self.pwcg_model_combo.setEnabled(False)
        self.pwcg_apply_btn: QPushButton = QPushButton("Aplicar Modelo")
        self.pwcg_apply_btn.setEnabled(False)
        self.pwcg_apply_btn.clicked.connect(self._apply_pwcg_model)
        
        pwcg_row: QHBoxLayout = QHBoxLayout()
        pwcg_row.addWidget(self.use_pwcg_chk)
        pwcg_row.addWidget(self.pwcg_model_combo, 1)
        pwcg_row.addWidget(self.pwcg_apply_btn)
        pwcg_row_wrap: QWidget = QWidget()
        pwcg_row_wrap.setLayout(pwcg_row)
        
        # Campo: Condições
        self.cond_list_widget: QTextEdit = QTextEdit()
        self.cond_list_widget.setPlaceholderText("Cada condição por linha: descrição | tipo | valor")
        self.cond_list_widget.setMinimumHeight(90)
        
        # Label de erro
        self.error_label: QLabel = QLabel("")
        self.error_label.setStyleSheet("color:red; font-weight:bold")
        
        # Botões do formulário
        btns: QHBoxLayout = QHBoxLayout()
        btns.addStretch()
        self.btn_cancel: QPushButton = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self._hide_form)
        self.btn_save: QPushButton = QPushButton("Salvar")
        self.btn_save.clicked.connect(self._save_medal)
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_save)
        btns_wrap: QWidget = QWidget()
        btns_wrap.setLayout(btns)
        
        # Montagem do formulário
        form.addRow("Nome:", self.nome_input)
        form.addRow("Imagem:", img_wrap)
        form.addRow("Ribbon:", rib_wrap)
        form.addRow("Nação:", self.country_combo)
        form.addRow("Descrição:", self.descricao_edit)
        form.addRow(pwcg_row_wrap)
        form.addRow("Condições:", self.cond_list_widget)
        form.addRow(self.error_label)
        form.addRow(btns_wrap)
        
        layout.addWidget(self.form_group)
    
    def _ensure_dirs(self) -> None:
        """Garante que os diretórios de assets existam."""
        try:
            self._assets_meta_dir.mkdir(parents=True, exist_ok=True)
            self._assets_images_dir.mkdir(parents=True, exist_ok=True)
            self._assets_ribbons_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Diretórios de assets verificados/criados")
        except OSError as e:
            logger.error(f"Erro ao criar diretórios de assets: {e}")
            QMessageBox.critical(
                self, 
                "Erro de Diretório", 
                f"Não foi possível criar os diretórios necessários:\n{e}"
            )
    
    def set_pwcgfc_path(self, pwcgfc_path: str) -> None:
        """Define o caminho do PWCGFC para importação de modelos de condições.
        
        Args:
            pwcgfc_path: Caminho do diretório raiz do PWCGFC
        """
        self._pwcgfc_path = Path(pwcgfc_path) if pwcgfc_path else None
        self._reload_pwcg_models()
    
    def _reload_pwcg_models(self) -> None:
        """Carrega modelos de condições dos arquivos JSON do PWCG."""
        self._pwcg_models = []
        self.pwcg_model_combo.clear()
        
        if not self._pwcgfc_path:
            logger.debug("Caminho PWCGFC não definido; modelos não carregados")
            return
        
        base: Path = self._pwcgfc_path / "FCData" / "Input"
        if not base.exists():
            logger.warning(f"Diretório PWCG Input não encontrado: {base}")
            return
        
        models_found = 0
        for p in base.rglob("*.json"):
            try:
                data: Dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
                logger.warning(f"Não foi possível ler ou decodificar o arquivo {p}: {e}")
                continue
            
            # Busca por arrays de condições em chaves conhecidas
            candidates: List[Tuple[str, List[Dict[str, Any]]]] = []
            if isinstance(data, dict):
                for k in ("awardConditions", "conditions", "medalConditions"):
                    v = data.get(k)
                    if isinstance(v, list) and v:
                        candidates.append((k, v))
            
            if not candidates:
                continue
            
            for key, arr in candidates:
                conds: List[Dict[str, Any]] = []
                for it in arr:
                    if not isinstance(it, dict):
                        continue
                    
                    desc = str(it.get("descricao") or it.get("description") or it.get("desc") or "").strip()
                    typ = str(it.get("tipo") or it.get("type") or it.get("category") or "").strip()
                    val = it.get("valor", it.get("value", ""))
                    conds.append({"descricao": desc, "tipo": typ, "valor": str(val)})
                
                if conds:
                    label = f"{p.stem}::{key} ({len(conds)})"
                    self._pwcg_models.append({"label": label, "condicoes": conds})
                    self.pwcg_model_combo.addItem(label, len(self._pwcg_models) - 1)
                    models_found += 1
        
        logger.info(f"Carregados {models_found} modelos de condições do PWCG")
    
    def _toggle_pwcg_models(self) -> None:
        """Habilita/desabilita controles de modelos PWCG baseado no checkbox."""
        enabled: bool = self.use_pwcg_chk.isChecked()
        self.pwcg_model_combo.setEnabled(enabled)
        self.pwcg_apply_btn.setEnabled(enabled)
    
    def _apply_pwcg_model(self) -> None:
        """Aplica o modelo PWCG selecionado ao campo de condições."""
        idx = self.pwcg_model_combo.currentData()
        if idx is None:
            return
        
        try:
            model: Dict[str, Any] = self._pwcg_models[int(idx)]
        except (IndexError, ValueError, TypeError):
            logger.warning(f"Índice de modelo PWCG inválido: {idx}")
            return
        
        lines: List[str] = [
            f"{c['descricao']}|{c['tipo']}|{c['valor']}" 
            for c in model.get("condicoes", [])
        ]
        self.cond_list_widget.setPlainText("\n".join(lines))
        logger.debug(f"Modelo PWCG aplicado: {model.get('label')}")
    
    def _load_medals(self) -> None:
        """Carrega medalhas do arquivo JSON com auto-healing e backup em caso de erro."""
        self.medals.clear()
        
        try:
            # Garante diretório e arquivo
            self._assets_meta_dir.mkdir(parents=True, exist_ok=True)
            if not self._meta_file.exists():
                self._meta_file.write_text("[]\n", encoding="utf-8")
                logger.info("Arquivo medals.json inicializado vazio")
            
            raw: str = self._meta_file.read_text(encoding="utf-8")
            
            if not raw.strip():
                # Arquivo vazio: inicializa com []
                self._meta_file.write_text("[]\n", encoding="utf-8")
                self.medals = []
                logger.warning("medals.json estava vazio; reiniciado")
            else:
                data: Any = json.loads(raw)
                self.medals = data if isinstance(data, list) else []
                logger.info(f"Carregadas {len(self.medals)} medalhas")
        
        except json.JSONDecodeError as e:
            # Backup do arquivo corrompido
            try:
                backup: Path = self._meta_file.with_suffix(".json.bak")
                shutil.copyfile(self._meta_file, backup)
                logger.error(f"medals.json inválido; backup em {backup}: {e}")
                QMessageBox.warning(
                    self, 
                    "Aviso",
                    f"Arquivo de medalhas inválido. Um backup foi salvo em:\n{backup}\n"
                    "O arquivo será reiniciado vazio."
                )
            except (OSError, shutil.Error) as be:
                logger.error(f"Falha ao criar backup do medals.json: {be}")
                QMessageBox.warning(
                    self, 
                    "Aviso",
                    "Arquivo de medalhas inválido. Não foi possível criar um backup.\n"
                    "O arquivo será reiniciado vazio."
                )
            
            # Reinicia arquivo
            try:
                self._meta_file.write_text("[]\n", encoding="utf-8")
            except OSError as we:
                logger.exception(f"Falha ao regravar medals.json vazio: {we}")
                QMessageBox.critical(
                    self, 
                    "Erro Crítico", 
                    "Não foi possível recriar o arquivo de medalhas. "
                    "Verifique as permissões do diretório."
                )
            self.medals = []
        
        except (OSError, UnicodeDecodeError) as e:
            logger.exception(f"Falha ao ler manifesto de medalhas: {e}")
            QMessageBox.critical(
                self, 
                "Erro de Leitura", 
                f"Não foi possível ler o arquivo de medalhas:\n{e}"
            )
            self.medals = []
        
        finally:
            self._refresh_list()
    
    def _refresh_list(self) -> None:
        """Atualiza a tabela de medalhas com os dados atuais."""
        self.table.setRowCount(len(self.medals))
        
        for i, m in enumerate(self.medals):
            # Coluna Nome
            self.table.setItem(i, 0, QTableWidgetItem(m.get("nome", "")))
            
            # Coluna Imagem
            medal_pix: QLabel = QLabel()
            mp: QPixmap = self._resolve_asset_pixmap(m.get("imagem_path", ""))
            if not mp.isNull():
                medal_pix.setPixmap(mp.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.table.setCellWidget(i, 1, medal_pix)
            
            # Coluna Ribbon
            rib_pix: QLabel = QLabel()
            rp: QPixmap = self._resolve_asset_pixmap(m.get("ribbon_path", ""))
            if not rp.isNull():
                rib_pix.setPixmap(rp.scaled(48, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.table.setCellWidget(i, 2, rib_pix)
            
            # Coluna Editar
            btn_edit: QPushButton = QPushButton("Editar")
            btn_edit.clicked.connect(lambda _, idx=i: self._show_form_edit(idx))
            self.table.setCellWidget(i, 3, btn_edit)
    
    def _resolve_asset_pixmap(self, rel_or_abs: str) -> QPixmap:
        """Resolve caminho de asset e retorna QPixmap.
        
        Args:
            rel_or_abs: Caminho absoluto ou relativo ao diretório de assets
            
        Returns:
            QPixmap carregado ou vazio se não encontrado
        """
        if not rel_or_abs:
            return QPixmap()
        
        p: Path = Path(rel_or_abs)
        if p.is_absolute():
            return QPixmap(str(p))
        return QPixmap(str(self._assets_root / rel_or_abs))
    
    def _select_img(self) -> None:
        """Abre diálogo para seleção de imagem da medalha."""
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Selecionar Imagem da Medalha", 
            "", 
            "Imagens (*.png *.jpg *.jpeg)"
        )
        if path:
            self.img_path_input.setText(path)
    
    def _select_ribbon(self) -> None:
        """Abre diálogo para seleção de ribbon (opcional)."""
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Selecionar Ribbon (opcional)", 
            "", 
            "Imagens (*.png *.jpg *.jpeg)"
        )
        if path:
            self.ribbon_path_input.setText(path)
    
    def _show_form_add(self) -> None:
        """Exibe formulário para adicionar nova medalha."""
        self.selected_idx = None
        self.nome_input.clear()
        self.img_path_input.clear()
        self.ribbon_path_input.clear()
        self.country_combo.setCurrentIndex(0)
        self.descricao_edit.clear()
        self.cond_list_widget.clear()
        self.error_label.clear()
        self.form_group.setTitle("Cadastro de Medalha/Condecoração")
        self.form_group.setVisible(True)
    
    def _show_form_edit(self, idx: int) -> None:
        """Exibe formulário para editar medalha existente.
        
        Args:
            idx: Índice da medalha na lista
        """
        self.selected_idx = idx
        m: Dict[str, Any] = self.medals[idx]
        
        self.nome_input.setText(m.get("nome", ""))
        
        img_path = m.get("imagem_path", "")
        self.img_path_input.setText(
            str(self._assets_root / img_path) if img_path else ""
        )
        
        rib_path = m.get("ribbon_path", "")
        self.ribbon_path_input.setText(
            str(self._assets_root / rib_path) if rib_path else ""
        )
        
        self.country_combo.setCurrentText(
            (m.get("country") or "").strip().lower() or "germany"
        )
        self.descricao_edit.setPlainText(m.get("descricao", ""))
        
        # Condições
        cond_lines = "\n".join(
            f"{c.get('descricao','')}|{c.get('tipo','')}|{c.get('valor','')}" 
            for c in m.get("condicoes", [])
        )
        self.cond_list_widget.setPlainText(cond_lines)
        
        self.error_label.clear()
        self.form_group.setTitle("Edição de Medalha/Condecoração")
        self.form_group.setVisible(True)
    
    def _hide_form(self) -> None:
        """Oculta o formulário de cadastro/edição."""
        self.form_group.setVisible(False)
    
    def _save_medal(self) -> None:
        """Valida e salva medalha (nova ou editada)."""
        nome: str = self.nome_input.text().strip()
        img_src: str = self.img_path_input.text().strip()
        rib_src: str = self.ribbon_path_input.text().strip()
        country: str = self.country_combo.currentText().strip().lower()
        descricao: str = self.descricao_edit.toPlainText().strip()
        cond_lines: List[str] = [
            ln.strip() 
            for ln in self.cond_list_widget.toPlainText().splitlines() 
            if ln.strip()
        ]
        
        # Validações
        erros: List[str] = []
        
        # Validação: Nome
        if not nome:
            erros.append("O nome é obrigatório.")
        elif any(
            m["nome"].strip().lower() == nome.lower()
            for i, m in enumerate(self.medals)
            if i != (self.selected_idx if self.selected_idx is not None else -1)
        ):
            erros.append("Já existe medalha com este nome.")
        
        # Validação: Imagem
        if not img_src or not img_src.lower().endswith((".png", ".jpg", ".jpeg")):
            erros.append("Imagem da medalha é obrigatória (PNG/JPG).")
        elif not Path(img_src).exists():
            erros.append("Arquivo de imagem da medalha não encontrado.")
        
        # Validação: Ribbon (opcional)
        if rib_src:
            if not rib_src.lower().endswith((".png", ".jpg", ".jpeg")) or not Path(rib_src).exists():
                erros.append("Ribbon inválida: informe arquivo PNG/JPG existente ou deixe em branco.")
        
        # Validação: Condições
        condicoes: List[Dict[str, Any]] = []
        for i, ln in enumerate(cond_lines, 1):
            parts: List[str] = [p.strip() for p in ln.split("|")]
            if len(parts) != 3 or not all(parts):
                erros.append(f"Condição {i}: use 'descrição | tipo | valor'.")
                continue
            condicoes.append({"descricao": parts[0], "tipo": parts[1], "valor": parts[2]})
        
        if not condicoes:
            erros.append("Inclua pelo menos uma condição completa.")
        
        if erros:
            self.error_label.setText("\n".join(erros))
            logger.warning(f"Validação falhou ao salvar medalha: {erros}")
            return
        
        # Cópia de arquivos para diretório de assets
        try:
            self._assets_images_dir.mkdir(parents=True, exist_ok=True)
            self._assets_ribbons_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Erro ao criar diretórios de assets: {e}")
            self.error_label.setText(f"Erro ao criar diretórios: {e}")
            return
        
        # Copia imagem
        medal_dst: Path = self._assets_images_dir / Path(img_src).name
        if not medal_dst.exists():
            try:
                shutil.copyfile(img_src, medal_dst)
                logger.info(f"Imagem copiada: {medal_dst.name}")
            except (OSError, shutil.Error) as e:
                logger.error(f"Falha ao copiar imagem: {str(e)}")
                self.error_label.setText(f"Falha ao copiar imagem: {str(e)}")
                return
        
        # Copia ribbon (se houver)
        ribbon_rel: str = ""
        if rib_src:
            ribbon_dst: Path = self._assets_ribbons_dir / Path(rib_src).name
            if not ribbon_dst.exists():
                try:
                    shutil.copyfile(rib_src, ribbon_dst)
                    logger.info(f"Ribbon copiada: {ribbon_dst.name}")
                except (OSError, shutil.Error) as e:
                    logger.error(f"Falha ao copiar ribbon: {str(e)}")
                    self.error_label.setText(f"Falha ao copiar ribbon: {str(e)}")
                    return
            ribbon_rel = str(ribbon_dst.relative_to(self._assets_root))
        
        medal_rel: str = str(medal_dst.relative_to(self._assets_root))
        
        # Monta dicionário da medalha
        medal_data: Dict[str, Any] = {
            "nome": nome,
            "imagem_path": medal_rel,
            "ribbon_path": ribbon_rel,
            "descricao": descricao,
            "condicoes": condicoes,
            "country": country
        }
        
        # Atualiza ou adiciona medalha
        if self.selected_idx is not None:
            self.medals[self.selected_idx] = medal_data
            updated_index: int = self.selected_idx
            self.selected_idx = None
            self._persist_and_feedback()
            self.medal_updated.emit(updated_index, medal_data)
            logger.info(f"Medalha atualizada: {nome} (idx {updated_index})")
        else:
            self.medals.append(medal_data)
            self._persist_and_feedback()
            self.medal_added.emit(medal_data)
            logger.info(f"Medalha adicionada: {nome}")
    
    def _persist_and_feedback(self) -> None:
        """Persiste medalhas em arquivo JSON com escrita atômica e exibe feedback."""
        try:
            with atomic_json_write(self._meta_file) as f:
                payload: str = json.dumps(self.medals, ensure_ascii=False, indent=2)
                f.write(payload + "\n")
            
            logger.info(f"Arquivo medals.json persistido ({len(self.medals)} medalhas)")
        except (OSError, TypeError, ValueError) as e:
            self.error_label.setText(f"Falha ao salvar arquivo: {e}")
            logger.exception("Falha na gravação atômica do medals.json")
            QMessageBox.critical(
                self,
                "Erro ao Salvar",
                f"Não foi possível salvar o arquivo de medalhas:\n{e}"
            )
            return
        
        self._hide_form()
        self._refresh_list()
        QMessageBox.information(self, "Salvar", "Medalha salva com sucesso!")
