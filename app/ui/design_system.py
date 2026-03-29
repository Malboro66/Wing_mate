# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - app/ui/design_system.py
# Compatibility shim — all symbols live in design_system_v3.py
# ===================================================================
from __future__ import annotations

from app.ui.design_system_v3 import (  # noqa: F401
    DarkColors,
    LightColors,
    DSColors,
    DSStyles,
    DSStates,
    DSSpacing,
    DSFeedback,
    _refresh_feedback,
    _svg_chevron,
    load_custom_fonts,
    font_display,
    font_ui,
    font_body,
    current_theme,
    set_theme,
    build_global_stylesheet,
    apply_primary_button,
    apply_ghost_button,
    apply_danger_button,
    apply_section_group,
)

__all__ = [
    "DarkColors",
    "LightColors",
    "DSColors",
    "DSStyles",
    "DSStates",
    "DSSpacing",
    "DSFeedback",
    "_refresh_feedback",
    "_svg_chevron",
    "load_custom_fonts",
    "font_display",
    "font_ui",
    "font_body",
    "current_theme",
    "set_theme",
    "build_global_stylesheet",
    "apply_primary_button",
    "apply_ghost_button",
    "apply_danger_button",
    "apply_section_group",
]
