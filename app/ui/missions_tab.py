# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - app/ui/missions_tab.py
# Aba de Missões com dia da semana em INGLÊS
# ===================================================================

from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QTableWidget, QTableWidgetItem,
    QTextEdit, QGroupBox, QHeaderView
)


class MissionsTab(QWidget):
    """Aba de Missões com tabela e painel de detalhes."""
    
    missionSelected = pyqtSignal(int, object)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Inicializa a aba de missões."""
        super().__init__(parent)
        self._missions: List[Dict[str, Any]] = []
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Constrói a interface da aba de missões."""
        layout: QVBoxLayout = QVBoxLayout(self)
        splitter: QSplitter = QSplitter(Qt.Vertical, self)
        
        # Tabela de missões
        self.table: QTableWidget = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            self.tr("Data"), 
            self.tr("Hora"), 
            self.tr("Aeronave"), 
            self.tr("Tipo")
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Painel de detalhes
        details_group: QGroupBox = QGroupBox(self.tr("Detalhes da Missão Selecionada"))
        details_layout: QVBoxLayout = QVBoxLayout(details_group)
        self.details: QTextEdit = QTextEdit()
        self.details.setReadOnly(True)
        details_layout.addWidget(self.details)
        
        splitter.addWidget(self.table)
        splitter.addWidget(details_group)
        splitter.setSizes([400, 200])
        layout.addWidget(splitter)
    
    def set_missions(self, missions: List[Dict[str, Any]]) -> None:
        """
        Define a lista de missões a ser exibida na tabela.
        
        Args:
            missions: Lista de dicionários, onde cada dicionário representa uma missão.
        """
        self._missions = missions if isinstance(missions, list) else []
        self.table.setRowCount(len(self._missions))
        
        for r, m in enumerate(self._missions):
            if not isinstance(m, dict):
                continue
            
            # Coluna 0: Data
            date_value = str(m.get('date', ''))
            date_item = QTableWidgetItem(date_value)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 0, date_item)
            
            # Coluna 1: Hora (extraída)
            formatted_time = self._extract_time(m)
            time_item = QTableWidgetItem(formatted_time)
            time_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 1, time_item)
            
            # Coluna 2: Aeronave
            aircraft = str(m.get('aircraft', ''))
            aircraft_item = QTableWidgetItem(aircraft)
            aircraft_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 2, aircraft_item)
            
            # Coluna 3: Tipo de missão
            duty = str(m.get('duty', ''))
            duty_item = QTableWidgetItem(duty)
            duty_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 3, duty_item)
        
        self.details.clear()
    
    def _extract_time(self, mission: Dict[str, Any]) -> str:
        """
        Extrai a hora da missão de múltiplas fontes possíveis.
        
        Args:
            mission: Dicionário com dados da missão
            
        Returns:
            Hora formatada como HH:MM ou string vazia
        """
        # Tenta campo 'time' primeiro
        time_value = mission.get('time', '')
        formatted = self._format_time(time_value)
        if formatted:
            return formatted
        
        # Se não encontrou, tenta extrair de 'description'
        description = str(mission.get('description', ''))
        if description:
            # Procura por padrão "Time: HH:MM:SS" ou "Time HH:MM"
            time_match = re.search(r'Time[:\s]+(\d{1,2}):(\d{2})(?::(\d{2}))?', description, re.IGNORECASE)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return f"{hour:02d}:{minute:02d}"
        
        return ''
    
    def _format_time(self, time_value: Any) -> str:
        """
        Formata o valor de hora para exibição como HH:MM.
        
        Args:
            time_value: Valor da hora (pode ser string, datetime, etc)
            
        Returns:
            Hora formatada como string (HH:MM) ou string vazia se inválido
        """
        if not time_value:
            return ''
        
        time_str = str(time_value).strip()
        
        # Ignora se parece ser uma data (formato d.m.yyyy)
        if re.match(r'^\d{1,2}\.\d{1,2}\.\d{4}$', time_str):
            return ''
        
        # Caso 1: Formato "HH:MM:SS" ou "HH:MM"
        if ':' in time_str:
            # Remove parte de data se existir (ex: "1.1.1916 11:00:00")
            if ' ' in time_str:
                time_str = time_str.split(' ')[-1]
            
            parts = time_str.split(':')
            if len(parts) >= 2:
                try:
                    hour = int(parts[0])
                    minute = int(parts[1])
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return f"{hour:02d}:{minute:02d}"
                except ValueError:
                    pass
        
        # Caso 2: Tenta parsear como datetime
        for fmt in [
            '%H:%M:%S',
            '%H:%M',
            '%d.%m.%Y %H:%M:%S',
            '%d.%m.%Y %H:%M',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M'
        ]:
            try:
                dt = datetime.strptime(time_str, fmt)
                return dt.strftime('%H:%M')
            except ValueError:
                continue
        
        return ''
    
    def _get_weekday(self, date_str: str) -> str:
        """
        Retorna o dia da semana em INGLÊS para uma data.
        
        Args:
            date_str: Data no formato "DD/MM/YYYY" ou "D.M.YYYY"
            
        Returns:
            Dia da semana em inglês (Monday, Tuesday, etc.) ou string vazia se inválido
        """
        if not date_str:
            return ''
        
        # Tenta formatos comuns
        for fmt in ['%d/%m/%Y', '%d.%m.%Y', '%d-%m-%Y']:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                # Retorna dia da semana em inglês
                return date_obj.strftime('%A')  # ✅ Retorna em inglês: Monday, Tuesday, etc.
            except ValueError:
                continue
        
        return ''
    
    def selected_index(self) -> int:
        """
        Retorna o índice da linha selecionada na tabela.
        
        Returns:
            O índice da linha selecionada, ou -1 se nenhuma estiver selecionada.
        """
        return self.table.currentRow()
    
    def _on_selection_changed(self) -> None:
        """
        Lida com a mudança de seleção na tabela de missões.
        Atualiza o painel de detalhes e emite sinal com dia da semana em inglês.
        """
        idx: int = self.selected_index()
        
        if 0 <= idx < len(self._missions):
            data: Dict[str, Any] = self._missions[idx]
            description = str(data.get('description', ''))
            
            # ADICIONA DIA DA SEMANA EM INGLÊS
            date_str = str(data.get('date', ''))
            weekday = self._get_weekday(date_str)
            
            if weekday:
                # Injeta o dia da semana logo após "Date: X.X.XXXX"
                date_match = re.search(r'(Date[:\s]+\d{1,2}\.\d{1,2}\.\d{4})', description)
                if date_match:
                    date_line = date_match.group(1)
                    # Adiciona dia da semana em inglês após a data
                    enhanced_description = description.replace(
                        date_line,
                        f"{date_line} ({weekday})"
                    )
                    self.details.setText(enhanced_description)
                else:
                    self.details.setText(description)
            else:
                self.details.setText(description)
            
            self.missionSelected.emit(idx, data)
        else:
            self.details.clear()
            self.missionSelected.emit(-1, {})
