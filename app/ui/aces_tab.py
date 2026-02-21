# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - app/ui/aces_tab.py
# Aba de Ases com roundels PNG e sem edição
# ===================================================================

from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from app.ui.widgets.stats_bar import StatsBar
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QLabel, QAbstractItemView
)

logger = logging.getLogger("IL2CampaignAnalyzer")


class AcesTab(QWidget):
    stats_updated = pyqtSignal(int, int, str, int)
    """Aba de Ases da campanha com roundels por nacionalidade."""
    
    # Tamanhos otimizados
    ROUNDEL_SIZE = 45
    ROW_HEIGHT = 60
    ROUNDEL_COLUMN_WIDTH = 70
    
    # ✅ CORRIGIDO: Mapeamento para arquivos PNG
    COUNTRY_ROUNDELS = {
        'GERMANY': 'theme_german.png',
        'BRITAIN': 'theme_rfc.png',
        'FRANCE': 'theme_french.png',
        'USA': 'theme_american.png',
        'BELGIAN': 'theme_belgium.png',
        'BELGIUM': 'theme_belgium.png'
    }
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Inicializa a aba de Ases."""
        super().__init__(parent)
        
        layout: QVBoxLayout = QVBoxLayout(self)

        self._stats_bar = StatsBar([
            ("Total", "0"),
            ("Elegíveis", "0"),
            ("Top Ás", "—"),
            ("Top Vitórias", "0"),
        ])
        layout.addWidget(self._stats_bar)
        self.stats_updated.connect(self._on_stats_updated, Qt.QueuedConnection)

        # Tabela com 4 colunas
        self.table: QTableWidget = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Ás", 
            "Patente",
            "Nacionalidade",
            "Vitórias"
        ])
        
        # ✅ DESABILITA EDIÇÃO
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Configura redimensionamento
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.table.setColumnWidth(2, self.ROUNDEL_COLUMN_WIDTH)
        self.table.verticalHeader().setDefaultSectionSize(self.ROW_HEIGHT)
        
        layout.addWidget(self.table)
    
    def set_aces(self, aces: List[Dict[str, Any]]) -> None:
        """Define a lista de ases a ser exibida na tabela."""
        aces = aces or []
        
        # Filtro: Apenas pilotos com 5+ vitórias
        filtered_aces = [
            ace for ace in aces 
            if self._get_victories(ace) >= 5
        ]
        
        # Ordena por número de vitórias (decrescente)
        filtered_aces.sort(key=lambda x: self._get_victories(x), reverse=True)
        
        logger.info(f"Exibindo {len(filtered_aces)} ases com 5+ vitórias")
        
        self.table.setRowCount(len(filtered_aces))

        top_name = str(filtered_aces[0].get("name", "—")) if filtered_aces else "—"
        top_victories = self._get_victories(filtered_aces[0]) if filtered_aces else 0
        self.stats_updated.emit(len(aces), len(filtered_aces), top_name, top_victories)

        for r, ace in enumerate(filtered_aces):
            # Coluna 0: Nome do piloto
            name = str(ace.get("name", "N/A"))
            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.table.setItem(r, 0, name_item)
            
            # Coluna 1: Patente
            rank = str(ace.get("rank", "N/A")).strip()
            rank_item = QTableWidgetItem(rank if rank else "N/A")
            rank_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.table.setItem(r, 1, rank_item)
            
            # Coluna 2: NACIONALIDADE (ROUNDEL COM WIDGET)
            country_code = str(ace.get("country", "")).strip().upper()
            roundel_widget = self._create_roundel_widget(country_code)
            
            if roundel_widget:
                self.table.setCellWidget(r, 2, roundel_widget)
            else:
                # Fallback: mostra código do país se roundel não disponível
                fallback_text = country_code if country_code else "N/A"
                country_item = QTableWidgetItem(fallback_text)
                country_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                self.table.setItem(r, 2, country_item)
            
            # Coluna 3: Vitórias
            victories = str(self._get_victories(ace))
            victories_item = QTableWidgetItem(victories)
            victories_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.table.setItem(r, 3, victories_item)
    
    def _on_stats_updated(self, total: int, eligible: int, top_name: str, top_victories: int) -> None:
        self._stats_bar.update_stat("Total", str(total))
        self._stats_bar.update_stat("Elegíveis", str(eligible))
        self._stats_bar.update_stat("Top Ás", top_name or "—")
        self._stats_bar.update_stat("Top Vitórias", str(top_victories))

    def _create_roundel_widget(self, country_code: str) -> Optional[QLabel]:
        """
        Cria um QLabel com a roundel do país.
        
        Args:
            country_code: Código do país em maiúsculas
            
        Returns:
            QLabel com roundel ou None se não encontrado
        """
        if not country_code:
            return None
        
        # Busca arquivo de roundel
        roundel_filename = self.COUNTRY_ROUNDELS.get(country_code)
        if not roundel_filename:
            logger.warning(f"Roundel não mapeada para país: {country_code}")
            return None
        
        # Caminho: app/assets/icons/
        base_path = Path(__file__).resolve().parents[1] / "assets" / "icons"
        roundel_path = base_path / roundel_filename
        
        if not roundel_path.exists():
            logger.warning(f"Arquivo de roundel não encontrado: {roundel_path}")
            return None
        
        # Carrega pixmap
        pixmap = QPixmap(str(roundel_path))
        if pixmap.isNull():
            logger.warning(f"Falha ao carregar imagem: {roundel_path}")
            return None
        
        # Cria label
        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        
        # Redimensiona mantendo proporção
        scaled_pixmap = pixmap.scaled(
            self.ROUNDEL_SIZE, 
            self.ROUNDEL_SIZE, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        label.setPixmap(scaled_pixmap)
        label.setFixedSize(self.ROUNDEL_COLUMN_WIDTH, self.ROW_HEIGHT)
        
        return label
    
    def _get_victories(self, ace: Dict[str, Any]) -> int:
        """
        Extrai o número de vitórias de um as.
        
        Args:
            ace: Dicionário com dados do as
            
        Returns:
            Número de vitórias (inteiro)
        """
        victories = ace.get("victories", 0)
        
        # Se victories for um número direto
        try:
            return int(victories)
        except (ValueError, TypeError):
            return 0
