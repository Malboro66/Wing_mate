# -*- coding: utf-8 -*-
"""Design system mínimo para tokens visuais reutilizáveis em PyQt."""

from __future__ import annotations

from PyQt5.QtWidgets import QGroupBox, QPushButton


class DSColors:
    TEXT_MUTED = "#888"
    BORDER_DEFAULT = "#444"
    BORDER_DASHED = "#666"
    BG_PANEL = "#1e1e1e"


class DSStyles:
    PANEL_PLACEHOLDER = (
        f"color:{DSColors.TEXT_MUTED}; "
        f"border:1px solid {DSColors.BORDER_DEFAULT}; "
        f"background:{DSColors.BG_PANEL};"
    )
    PANEL_DASHED_PLACEHOLDER = (
        f"color:{DSColors.TEXT_MUTED}; border:1px dashed {DSColors.BORDER_DASHED};"
    )
    STATE_INFO = "color:#d8d8d8; background:#2a2a2a; border:1px solid #4a4a4a; padding:6px;"
    STATE_SUCCESS = "color:#dff5df; background:#1f3a1f; border:1px solid #2d6a2d; padding:6px;"
    STATE_WARNING = "color:#ffe9c4; background:#3b2f1f; border:1px solid #7a5b2e; padding:6px;"
    STATE_ERROR = "color:#ffd6d6; background:#3a1f1f; border:1px solid #7a2e2e; padding:6px;"


class DSSpacing:
    ICON_PREVIEW_SIZE = 160


def apply_primary_button(button: QPushButton) -> None:
    button.setMinimumHeight(30)


def apply_section_group(group: QGroupBox) -> None:
    group.setFlat(False)


class DSStates:
    LOADING = "loading"
    EMPTY = "empty"
    ERROR = "error"
    SUCCESS = "success"
