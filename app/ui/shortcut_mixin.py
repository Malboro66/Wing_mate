from __future__ import annotations

from typing import Optional

from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QLineEdit, QShortcut, QWidget


class CtrlFFocusMixin:
    """Mixin para foco de filtro com Ctrl+F usando QShortcut."""

    def bind_ctrl_f_to_filter(self, owner: QWidget, filter_edit: Optional[QLineEdit]) -> None:
        if filter_edit is None:
            return

        shortcut = QShortcut(QKeySequence("Ctrl+F"), owner)
        shortcut.setContext(shortcut.WidgetWithChildrenShortcut)
        shortcut.activated.connect(filter_edit.setFocus)
        shortcut.activated.connect(filter_edit.selectAll)

        # Mantém referência viva no ciclo do widget
        if not hasattr(self, "_shortcuts"):
            self._shortcuts = []
        self._shortcuts.append(shortcut)
