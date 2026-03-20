from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from PyQt5.QtWidgets import QHBoxLayout, QLabel, QWidget

from app.ui.design_system import DSColors, DSStyles, DSFeedback, DSSpacing, DSStates


class StatCard(QWidget):
    def __init__(self, label: str, value: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(6)

        lbl = QLabel(f"{label}:")
        lbl.setStyleSheet(
            f"color:{DSColors.TEXT_MUTED}; font-size:9px; letter-spacing:1.5px;"
            f" text-transform:uppercase; background:transparent;"
        )

        self._val = QLabel(value)
        self._val.setStyleSheet(
            f"color:{DSColors.TEXT_PRIMARY}; font-size:15px; font-weight:700; background:transparent;"
        )

        layout.addWidget(lbl)
        layout.addWidget(self._val)
        self.setStyleSheet(f"""
            QWidget {{
                background: {DSColors.DEEP};
                border-right: 1px solid {DSColors.BORDER};
                padding: 0px;
            }}
        """)

    def update_value(self, value: str) -> None:
        self._val.setText(value)


class StatsBar(QWidget):
    def __init__(self, stats: List[Tuple[str, str]], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._cards: Dict[str, StatCard] = {}

        for label, value in stats:
            card = StatCard(label, value)
            self._cards[label] = card
            layout.addWidget(card)

        layout.addStretch(1)

    def update_stat(self, label: str, value: str) -> None:
        if label in self._cards:
            self._cards[label].update_value(value)
