from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class WarPropagandaPopup(QDialog):
    """Popup com estética de jornal de 1917 para celebrar sequência de vitórias."""

    def __init__(self, pilot_name: str, victories_last_7d: int, photo_path: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Gazeta da Frente - 1917")
        self.setModal(False)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.resize(560, 300)

        self.setStyleSheet(
            "QDialog{background:#f2e7c9; border:2px solid #5c4b2f;}"
            "QLabel#title{font-size:22px; font-weight:700; color:#2f2417;}"
            "QLabel#subtitle{font-size:12px; color:#4a3a25;}"
            "QLabel#body{font-size:14px; color:#2f2417;}"
            "QLabel#photo{background:#d8c9a1; border:1px dashed #5c4b2f; color:#4a3a25;}"
            "QPushButton{background:#5c4b2f; color:#fff; padding:6px 12px;}"
        )

        root = QVBoxLayout(self)

        title = QLabel("🗞️ GAZETA DA FRENTE — EDIÇÃO EXTRA")
        title.setObjectName("title")
        root.addWidget(title)

        subtitle = QLabel("Ano de 1917 • Correspondente de Guerra")
        subtitle.setObjectName("subtitle")
        root.addWidget(subtitle)

        body_row = QHBoxLayout()

        self.photo_label = QLabel("Foto do Piloto")
        self.photo_label.setObjectName("photo")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setFixedSize(170, 210)
        self._load_photo(photo_path)
        body_row.addWidget(self.photo_label)

        body = QLabel(
            f"{pilot_name or 'Piloto Anônimo'} alcançou {victories_last_7d} vitórias "
            "nos últimos 7 dias. Sua bravura inspira todo o esquadrão!"
        )
        body.setObjectName("body")
        body.setWordWrap(True)
        body_row.addWidget(body, 1)

        root.addLayout(body_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

    def _load_photo(self, photo_path: str) -> None:
        path = Path(str(photo_path or "").strip())
        if not path.exists() or not path.is_file():
            return
        pm = QPixmap(str(path))
        if pm.isNull():
            return
        self.photo_label.setPixmap(pm.scaled(self.photo_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
