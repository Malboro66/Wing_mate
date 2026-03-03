from __future__ import annotations

from typing import Callable, Dict, Tuple

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.application.app_config import AppConfig
from app.ui.design_system import DSStyles
from utils.notification_bus import notify_info, notify_warning


class SettingsWidget(QWidget):
    go_back = pyqtSignal()
    settings_changed = pyqtSignal()

    def __init__(self, t: Callable[[str], str], config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._t = t
        self._config = config
        self._fields: Dict[str, Tuple[QLabel, QLineEdit, QPushButton, QLabel, str]] = {}

        root = QVBoxLayout(self)
        root.setSpacing(8)

        root.addLayout(self._build_path_row(AppConfig.KEY_IL2_FC, "path_il2_fc"))
        root.addLayout(self._build_path_row(AppConfig.KEY_ROF, "path_rof"))
        root.addLayout(self._build_path_row(AppConfig.KEY_PWCG, "path_pwcg"))

        self.btn_save = QPushButton(self._t("save_settings"))
        self.btn_save.clicked.connect(self.save)
        root.addWidget(self.btn_save)

        root.addStretch(1)
        footer = QHBoxLayout()
        self.btn_back = QPushButton(self._t("back"))
        self.btn_back.clicked.connect(self.go_back.emit)
        footer.addWidget(self.btn_back)
        footer.addStretch(1)
        root.addLayout(footer)

        self.load_from_settings()

    def _build_path_row(self, key: str, label_key: str):
        row = QHBoxLayout()

        lbl = QLabel(self._t(label_key))
        row.addWidget(lbl)

        edit = QLineEdit()
        edit.textChanged.connect(lambda txt, k=key: self._on_path_changed(k, txt))
        row.addWidget(edit, 1)

        browse = QPushButton(self._t("browse"))
        browse.clicked.connect(lambda _=False, k=key, e=edit: self._browse_path(k, e))
        row.addWidget(browse)

        status = QLabel("-")
        row.addWidget(status)

        self._fields[key] = (lbl, edit, browse, status, label_key)
        return row

    def _browse_path(self, key: str, edit: QLineEdit) -> None:
        selected = QFileDialog.getExistingDirectory(self, self._t("select_folder"))
        if selected:
            edit.setText(selected)
            self._config.set_path(key, selected)
            self._validate_and_render(key)

    def _on_path_changed(self, key: str, text: str) -> None:
        self._config.set_path(key, text)
        self._validate_and_render(key)
        self.settings_changed.emit()

    def _validate_and_render(self, key: str) -> None:
        _lbl, _edit, _browse, status, _label_key = self._fields[key]
        result = self._config.path_status(key)
        if result.is_valid:
            status.setText(self._t("path_valid"))
            status.setStyleSheet(DSStyles.STATE_SUCCESS)
        else:
            status.setText(self._t("path_invalid"))
            status.setStyleSheet(DSStyles.STATE_ERROR)
            notify_warning(self._t("path_invalid_toast"))

    def load_from_settings(self) -> None:
        for key, (_lbl, edit, _browse, _status, _label_key) in self._fields.items():
            edit.blockSignals(True)
            edit.setText(self._config.get_path(key))
            edit.blockSignals(False)
            self._validate_and_render(key)

    def save(self) -> None:
        # já persistimos em tempo real via QSettings; o botão aqui confirma e notifica
        invalid = [k for k in self._fields.keys() if not self._config.path_status(k).is_valid]
        if invalid:
            notify_warning(self._t("path_invalid_toast"))
        else:
            notify_info(self._t("settings_saved"))
        self.settings_changed.emit()

    def retranslate(self) -> None:
        self.btn_save.setText(self._t("save_settings"))
        self.btn_back.setText(self._t("back"))
        for key, (lbl, _edit, browse, _status, label_key) in self._fields.items():
            lbl.setText(self._t(label_key))
            browse.setText(self._t("browse"))
            self._validate_and_render(key)
