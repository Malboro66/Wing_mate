# -*- coding: utf-8 -*-
# app/ui/widgets/empty_state.py
# Widget de estado vazio instrucional para abas sem dados carregados.

from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.design_system import DSColors, apply_ghost_button, font_body, font_ui


class EmptyStateWidget(QWidget):
    """
    Estado vazio instrucional exibido antes do primeiro carregamento de dados.

    Exibe ícone, título, descrição e botão de ação (CTA) opcional.
    Emite action_triggered quando o CTA é clicado.

    Signals:
        action_triggered: Emitido quando o botão de CTA é clicado.
    """

    action_triggered = pyqtSignal()

    def __init__(
        self,
        icon: str,
        title: str,
        body: str,
        cta_label: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Args:
            icon:      Caractere Unicode para o ícone (ex: '✈', '⚔', '★')
            title:     Título principal do estado vazio
            body:      Descrição instrucional (aceita texto longo com wordwrap)
            cta_label: Texto do botão de ação; se vazio, botão não é criado
            parent:    Widget pai opcional
        """
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignCenter)
        root.setSpacing(12)
        root.setContentsMargins(40, 40, 40, 40)

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            "font-size:32px; background:transparent;"
        )

        title_lbl = QLabel(title)
        title_lbl.setFont(font_ui(15, bold=True))
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(
            f"color:{DSColors.TEXT_PRIMARY}; background:transparent;"
        )

        body_lbl = QLabel(body)
        body_lbl.setFont(font_body(12))
        body_lbl.setAlignment(Qt.AlignCenter)
        body_lbl.setWordWrap(True)
        body_lbl.setMaximumWidth(420)
        body_lbl.setStyleSheet(
            f"color:{DSColors.TEXT_MUTED}; background:transparent;"
        )

        root.addWidget(icon_lbl)
        root.addWidget(title_lbl)
        root.addWidget(body_lbl)

        if cta_label:
            self._btn = QPushButton(cta_label)
            apply_ghost_button(self._btn)
            self._btn.clicked.connect(self.action_triggered)
            root.addSpacing(4)
            root.addWidget(self._btn, alignment=Qt.AlignCenter)
        else:
            self._btn = None

    def set_texts(self, title: str, body: str, cta_label: str = "") -> None:
        """
        Atualiza os textos do estado vazio em runtime (ex: ao trocar idioma).

        Args:
            title:     Novo título
            body:      Nova descrição
            cta_label: Novo texto do botão; ignorado se botão não foi criado
        """
        layout = self.layout()
        if layout.count() >= 2:
            title_item = layout.itemAt(1)
            if title_item and title_item.widget():
                title_item.widget().setText(title)
        if layout.count() >= 3:
            body_item = layout.itemAt(2)
            if body_item and body_item.widget():
                body_item.widget().setText(body)
        if self._btn and cta_label:
            self._btn.setText(cta_label)
