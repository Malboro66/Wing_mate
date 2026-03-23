# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Type, Any

if TYPE_CHECKING:
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import QGroupBox, QPushButton


class DarkColors:
    VOID = "#0f1114"
    SHADOW = "#141820"
    DEEP = "#1a1f2a"
    PANEL = "#1e2530"
    SURFACE = "#242c3a"
    LIFTED = "#2c3548"
    BORDER = "#303848"
    MUTED = "#3d4860"

    BRASS = "#b8832a"
    AMBER = "#d4a030"
    GOLD = "#f0b840"
    GOLD_GLOW = "rgba(208,160,48,0.12)"

    TEXT_PRIMARY = "#d8d0c0"
    TEXT_SECONDARY = "#a09080"
    TEXT_MUTED = "#605850"
    TEXT_ACCENT = "#e8c060"
    TAB_INACTIVE_TEXT = "#9a8878"
    TAB_HOVER_TEXT = "#c0b0a0"

    SUCCESS = "#2d6e3a"
    SUCCESS_TXT = "#7ec890"
    WARNING = "#7a5818"
    WARNING_TXT = "#e8b860"
    DANGER = "#6e2d2d"
    DANGER_TXT = "#e88080"
    INFO = "#2d4a6e"
    INFO_TXT = "#80b0e8"


class LightColors:
    VOID = "#f5f0e8"
    SHADOW = "#ebe2d4"
    DEEP = "#e7dccb"
    PANEL = "#efe6d8"
    SURFACE = "#f8f3ec"
    LIFTED = "#efe1cc"
    BORDER = "#ccb89c"
    MUTED = "#b19b7d"

    BRASS = "#8a5a20"
    AMBER = "#8a5a20"
    GOLD = "#b87828"
    GOLD_GLOW = "rgba(184,120,40,0.12)"

    TEXT_PRIMARY = "#1e1810"
    TEXT_SECONDARY = "#3a2e20"
    TEXT_MUTED = "#7a6a54"
    TEXT_ACCENT = "#8a5c10"
    TAB_INACTIVE_TEXT = "#5a4830"
    TAB_HOVER_TEXT = "#3a2e20"

    SUCCESS = "#2f6f3a"
    SUCCESS_TXT = "#1f5a2d"
    WARNING = "#8a6a2b"
    WARNING_TXT = "#6f4f17"
    DANGER = "#8c3f3f"
    DANGER_TXT = "#6a2626"
    INFO = "#3f5d8c"
    INFO_TXT = "#244878"


def _svg_chevron(color: str) -> str:
    """
    Gera um chevron SVG como data URI para uso em QSS image: url(...).

    Escapa '#' para '%23' porque QSS interpreta '#' como início de comentário
    dentro de url(). O SVG resultante é um 'V' de 12x12px com stroke arredondado.

    Args:
        color: Cor hexadecimal com '#', ex: '#605850'

    Returns:
        String data URI pronta para uso em QSS image: url(...)
    """
    c = color.replace("#", "%23")
    return (
        "data:image/svg+xml,"
        "%3Csvg xmlns='http://www.w3.org/2000/svg' "
        "width='12' height='12' viewBox='0 0 12 12'%3E"
        "%3Cpath d='M2 4L6 8L10 4' fill='none' "
        f"stroke='{c}' stroke-width='1.5' "
        "stroke-linecap='round' stroke-linejoin='round'/%3E"
        "%3C/svg%3E"
    )


def _build_styles(C) -> "type":
    class _Styles:
        PANEL_PLACEHOLDER = (
            f"color:{C.TEXT_MUTED}; border:1px solid {C.BORDER}; background:{C.PANEL};"
        )

        STATE_INFO = (
            f"color:{C.INFO_TXT}; background:rgba(45,74,110,0.20); border-left:3px solid {C.INFO_TXT}; "
            "padding:6px 10px; border-radius:1px;"
        )
        STATE_SUCCESS = (
            f"color:{C.SUCCESS_TXT}; background:rgba(45,110,58,0.20); border-left:3px solid {C.SUCCESS_TXT}; "
            "padding:6px 10px; border-radius:1px;"
        )
        STATE_WARNING = (
            f"color:{C.WARNING_TXT}; background:rgba(122,88,24,0.20); border-left:3px solid {C.WARNING_TXT}; "
            "padding:6px 10px; border-radius:1px;"
        )
        STATE_ERROR = (
            f"color:{C.DANGER_TXT}; background:rgba(110,45,45,0.20); border-left:3px solid {C.DANGER_TXT}; "
            "padding:6px 10px; border-radius:1px;"
        )

        TABLE = f"""
            QTableWidget {{
                background: {C.VOID};
                color: {C.TEXT_SECONDARY};
                border: none;
                gridline-color: {C.BORDER};
                selection-background-color: {C.GOLD_GLOW};
            }}
            QHeaderView::section {{
                background: {C.DEEP}; color: {C.TEXT_MUTED}; border:none;
                border-right:1px solid {C.BORDER}; border-bottom:1px solid {C.BORDER};
                padding: 6px 12px; font-size:9px; font-weight:600; letter-spacing:1.2px;
            }}
            QTableWidget::item {{ padding:6px 12px; border-bottom:1px solid {C.BORDER}; }}
            QTableWidget::item:selected {{ background:{C.GOLD_GLOW}; color:{C.TEXT_PRIMARY}; }}
        """

        TABLE_HIGH_CONTRAST = """
            QTableWidget { background:#080a0c; color:#f0ead8; border:none; gridline-color:#505060; }
            QHeaderView::section { background:#0f1218; color:#c0b8a0; border-bottom:1px solid #505060; padding:6px 12px; }
        """

        INPUT = f"""
            QLineEdit, QTextEdit, QPlainTextEdit, QDateEdit {{
                background: {C.SURFACE};
                color: {C.TEXT_PRIMARY};
                border: 1px solid {C.BORDER};
                border-radius: 2px;
                padding: 5px 10px;
                selection-background-color: {C.GOLD_GLOW};
            }}
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QDateEdit:focus {{ border-color: {C.BRASS}; }}
            QLineEdit::placeholder, QTextEdit::placeholder {{ color: {C.TEXT_MUTED}; }}
            QDateEdit::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 28px;
                border: none;
                background: transparent;
            }}
            QDateEdit::down-arrow {{
                image: url("{_svg_chevron(C.TEXT_MUTED)}");
                width: 12px;
                height: 12px;
            }}
            QDateEdit::down-arrow:hover {{
                image: url("{_svg_chevron(C.AMBER)}");
            }}
        """

        COMBO = f"""
            QComboBox {{
                background: {C.SURFACE};
                color: {C.TEXT_PRIMARY};
                border: 1px solid {C.BORDER};
                border-radius: 2px;
                padding: 4px 34px 4px 10px;
                min-height: 28px;
            }}
            QComboBox:hover {{
                border-color: {C.MUTED};
            }}
            QComboBox:focus {{
                border-color: {C.BRASS};
            }}
            QComboBox:on {{
                border-color: {C.BRASS};
                background: {C.LIFTED};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 28px;
                border: none;
                border-left: 1px solid {C.BORDER};
                background: transparent;
            }}
            QComboBox::drop-down:hover {{
                background: {C.GOLD_GLOW};
            }}
            QComboBox::down-arrow {{
                image: url("{_svg_chevron(C.TEXT_MUTED)}");
                width: 12px;
                height: 12px;
            }}
            QComboBox::down-arrow:hover {{
                image: url("{_svg_chevron(C.AMBER)}");
            }}
            QComboBox::down-arrow:on {{
                image: url("{_svg_chevron(C.GOLD)}");
            }}
            QComboBox::down-arrow:disabled {{
                image: url("{_svg_chevron(C.TEXT_MUTED)}");
                opacity: 0.4;
            }}
            QComboBox QAbstractItemView {{
                background: {C.PANEL};
                color: {C.TEXT_SECONDARY};
                border: 1px solid {C.BRASS};
                border-top: none;
                selection-background-color: {C.GOLD_GLOW};
                selection-color: {C.TEXT_PRIMARY};
                outline: none;
                padding: 4px 0;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 5px 12px;
                min-height: 26px;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background: {C.GOLD_GLOW};
                color: {C.TEXT_PRIMARY};
            }}
        """

        GROUP_BOX = f"""
            QGroupBox {{ color:{C.AMBER}; border:1px solid {C.BORDER}; border-top:2px solid {C.BRASS}; border-radius:2px; margin-top:14px; padding-top:12px; }}
            QGroupBox::title {{ subcontrol-origin:margin; subcontrol-position:top left; left:12px; padding:0 8px; color:{C.AMBER}; }}
        """
        TAB_WIDGET = f"""
            QTabWidget::pane {{
                border: none;
                background: {C.VOID};
            }}
            QTabBar::tab {{
                background: {C.SHADOW};
                color: {C.TAB_INACTIVE_TEXT};
                border: none;
                border-bottom: 3px solid transparent;
                padding: 9px 18px;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.8px;
                min-width: 80px;
            }}
            QTabBar::tab:selected {{
                color: {C.AMBER};
                border-bottom: 3px solid {C.AMBER};
                background: rgba(212,160,48,0.06);
                font-weight: 700;
            }}
            QTabBar::tab:hover:!selected {{
                color: {C.TAB_HOVER_TEXT};
                background: {C.DEEP};
                border-bottom: 3px solid {C.BORDER};
            }}
            QTabBar::tab:first {{
                margin-left: 8px;
            }}
            QTabBar::tab:disabled {{
                color: {C.TEXT_MUTED};
            }}
        """
        TOOLBAR = f"""
            QToolBar {{ background:{C.SHADOW}; border-bottom:1px solid {C.BRASS}; spacing:2px; padding:2px 12px; }}
            QToolButton, QToolBar QPushButton {{ background:transparent; color:{C.TEXT_SECONDARY}; border:1px solid transparent; border-radius:2px; padding:4px 10px; }}
            QToolButton:hover, QToolBar QPushButton:hover {{ color:{C.AMBER}; border-color:{C.BRASS}; background:{C.GOLD_GLOW}; }}
        """
        STATUS_BAR = f"QStatusBar {{ background:{C.SHADOW}; color:{C.TEXT_MUTED}; border-top:1px solid {C.BORDER}; }} QStatusBar::item {{ border:none; }}"
        MAIN_WINDOW = f"QMainWindow {{ background:{C.VOID}; }}"
        PROGRESS_BAR = f"""
            QProgressBar {{ background:{C.BORDER}; border:none; border-radius:2px; height:4px; color:transparent; }}
            QProgressBar::chunk {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {C.BRASS}, stop:1 {C.GOLD}); border-radius:2px; }}
        """

    return _Styles


_DarkStyles = _build_styles(DarkColors)
_LightStyles = _build_styles(LightColors)


class DSSpacing:
    ICON_PREVIEW_SIZE = 160
    BORDER_RADIUS = 2
    PADDING_SMALL = 6
    PADDING_MEDIUM = 12
    PADDING_LARGE = 20
    TABLE_ROW_HEIGHT = 36
    HEADER_HEIGHT = 44
    TAB_HEIGHT = 40
    FORM_LABEL_WIDTH = 160
    FORM_MAX_WIDTH = 680
    PROFILE_PANEL_W = 260


class DSStates:
    LOADING = "loading"
    EMPTY = "empty"
    ERROR = "error"
    SUCCESS = "success"


class DSFeedback:
    TOAST_LEVEL_STYLES = {
        "info": "",
        "warning": "",
        "error": "",
        "success": "",
    }
    LOADING_OVERLAY_BG = ""
    LOADING_TITLE_TEXT = ""
    LOADING_BAR_ACTIVE = ""
    LOADING_BAR_IDLE = ""


_ACTIVE_THEME = "dark"
DSColors: Type[DarkColors] | Type[LightColors] = DarkColors
DSStyles = _DarkStyles


def _refresh_feedback() -> None:
    DSFeedback.TOAST_LEVEL_STYLES = {
        "info": f"background:{DSColors.DEEP}; color:{DSColors.INFO_TXT}; border:1px solid {DSColors.INFO_TXT};",
        "warning": f"background:{DSColors.DEEP}; color:{DSColors.WARNING_TXT}; border:1px solid {DSColors.WARNING_TXT};",
        "error": f"background:{DSColors.DEEP}; color:{DSColors.DANGER_TXT}; border:1px solid {DSColors.DANGER_TXT};",
        "success": f"background:{DSColors.DEEP}; color:{DSColors.SUCCESS_TXT}; border:1px solid {DSColors.SUCCESS_TXT};",
    }
    DSFeedback.LOADING_OVERLAY_BG = f"background-color: rgba(10,12,14,0.88);"
    DSFeedback.LOADING_TITLE_TEXT = f"color:{DSColors.AMBER}; font-weight:600; font-size:13px; letter-spacing:1px;"
    DSFeedback.LOADING_BAR_ACTIVE = DSColors.AMBER
    DSFeedback.LOADING_BAR_IDLE = DSColors.BORDER


def set_theme(theme: str) -> None:
    global DSColors, DSStyles, _ACTIVE_THEME
    if str(theme).strip().lower() == "light":
        DSColors = LightColors
        DSStyles = _LightStyles
        _ACTIVE_THEME = "light"
    else:
        DSColors = DarkColors
        DSStyles = _DarkStyles
        _ACTIVE_THEME = "dark"
    _refresh_feedback()


def current_theme() -> str:
    return _ACTIVE_THEME


def load_custom_fonts() -> None:
    from PyQt5.QtGui import QFontDatabase

    fonts_dir = Path(__file__).resolve().parents[1] / "assets" / "fonts"
    for filename in ("old_english.ttf", "roboto.ttf"):
        p = fonts_dir / filename
        if p.exists():
            QFontDatabase.addApplicationFont(str(p))


def _font_family(preferred: str, fallback: str) -> str:
    from PyQt5.QtGui import QFontDatabase

    return preferred if preferred in QFontDatabase().families() else fallback


def font_display(size: int = 14, bold: bool = False) -> "QFont":
    from PyQt5.QtGui import QFont

    f = QFont(_font_family("Old English", "Times New Roman"), int(size))
    f.setBold(bool(bold))
    return f


def font_ui(size: int = 10, bold: bool = False) -> "QFont":
    from PyQt5.QtGui import QFont

    f = QFont(_font_family("Roboto", "Arial"), int(size))
    f.setBold(bool(bold))
    return f


def font_body(size: int = 12, bold: bool = False) -> "QFont":
    return font_ui(size=size, bold=bold)


def apply_primary_button(button: Any) -> None:
    button.setMinimumHeight(30)
    button.setStyleSheet(
        f"QPushButton{{background:{DSColors.BRASS}; color:{DSColors.VOID}; border:1px solid {DSColors.AMBER}; border-radius:{DSSpacing.BORDER_RADIUS}px; padding:6px 16px; font-weight:700;}}"
        f"QPushButton:hover{{background:{DSColors.AMBER}; border-color:{DSColors.GOLD};}}"
    )


def apply_ghost_button(button: Any) -> None:
    button.setMinimumHeight(28)
    button.setStyleSheet(
        f"QPushButton{{background:transparent; color:{DSColors.TEXT_SECONDARY}; border:1px solid {DSColors.BORDER}; border-radius:{DSSpacing.BORDER_RADIUS}px; padding:5px 12px;}}"
        f"QPushButton:hover{{color:{DSColors.AMBER}; border-color:{DSColors.BRASS}; background:{DSColors.GOLD_GLOW};}}"
    )


def apply_section_group(group: Any) -> None:
    group.setFlat(False)
    group.setStyleSheet(DSStyles.GROUP_BOX)


def build_global_stylesheet() -> str:
    return (
        DSStyles.MAIN_WINDOW
        + DSStyles.TOOLBAR
        + DSStyles.TAB_WIDGET
        + DSStyles.STATUS_BAR
        + DSStyles.TABLE
        + DSStyles.INPUT
        + DSStyles.COMBO
        + DSStyles.PROGRESS_BAR
        + DSStyles.GROUP_BOX
        + f"""
        QWidget {{
            background: {DSColors.VOID};
            color: {DSColors.TEXT_SECONDARY};
            font-size: 13px;
        }}
        QLabel {{ background: transparent; color: {DSColors.TEXT_SECONDARY}; }}
        QCheckBox {{ color: {DSColors.TEXT_SECONDARY}; spacing: 6px; }}
        QCheckBox::indicator {{ width:14px; height:14px; background:{DSColors.SURFACE}; border:1px solid {DSColors.BORDER}; border-radius:1px; }}
        QCheckBox::indicator:checked {{ background:{DSColors.BRASS}; border-color:{DSColors.AMBER}; }}
        QToolTip {{ background:{DSColors.PANEL}; color:{DSColors.TEXT_PRIMARY}; border:1px solid {DSColors.BRASS}; padding:4px 8px; border-radius:2px; }}
        """
    )


_refresh_feedback()
