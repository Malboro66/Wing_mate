from __future__ import annotations

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QLabel, QWidget

from app.ui.design_system import DSColors, DSStyles, DSFeedback, DSSpacing, DSStates, apply_primary_button, apply_ghost_button, apply_section_group, font_display, font_ui, font_body


class ToastWidget(QLabel):
    """Toast não-bloqueante para feedback ao usuário."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMargin(10)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setStyleSheet("border-radius:8px; padding:8px;")

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self.hide()

    def show_toast(self, level: str, message: str, timeout_ms: int) -> None:
        from app.ui.design_system import font_ui
        LEVEL_ICONS = {"info": "ℹ", "warning": "⚠", "error": "✗", "success": "✓"}
        icon = LEVEL_ICONS.get(level, "ℹ")
        base = DSFeedback.get_toast_style(level)
        self.setStyleSheet(
            f"QLabel {{ border-radius:2px; padding:8px 16px; {base} }}"
        )
        self.setFont(font_ui(10, bold=True))
        self.setText(f"{icon}  {message or ''}")

        parent = self.parentWidget()
        if parent is not None:
            max_width = max(300, int(parent.width() * 0.60))
            self.setMaximumWidth(max_width)
            self.adjustSize()
            x = max(8, (parent.width() - self.width()) // 2)
            y = max(8, parent.height() - self.height() - 18)
            self.move(x, y)

        self.raise_()
        self.show()
        self._timer.start(max(800, int(timeout_ms or 0)))
