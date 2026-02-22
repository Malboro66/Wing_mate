from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from PyQt5.QtWidgets import QHBoxLayout, QLabel, QWidget


class StatCard(QWidget):
    def __init__(self, label: str, value: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(6)

        lbl = QLabel(f"{label}:")
        lbl.setStyleSheet("color:#888; font-size:12px;")

        self._val = QLabel(value)
        self._val.setStyleSheet("color:#d8d8d8; font-size:13px; font-weight:bold;")

        layout.addWidget(lbl)
        layout.addWidget(self._val)
        self.setStyleSheet(
            "background:#2a2a2a; border:1px solid #3a3a3a;"
            "border-radius:4px;"
        )

    def update_value(self, value: str) -> None:
        self._val.setText(value)


class StatsBar(QWidget):
    def __init__(self, stats: List[Tuple[str, str]], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)
        self._cards: Dict[str, StatCard] = {}

        for label, value in stats:
            card = StatCard(label, value)
            self._cards[label] = card
            layout.addWidget(card)

        layout.addStretch(1)

    def update_stat(self, label: str, value: str) -> None:
        if label in self._cards:
            self._cards[label].update_value(value)
