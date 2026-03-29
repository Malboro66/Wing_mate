# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - app/ui/design_system.py
# Design System v3 — Dual Theme: Dark "Frontline" + Light "Field Manual"
# Fontes customizadas: Old English (display) + Roboto (UI/body)
# ===================================================================

from __future__ import annotations

from pathlib import Path
from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtWidgets import QGroupBox, QPushButton

# ───────────────────────────────────────────────────────────────────
# CAMINHOS DE FONTES
# ───────────────────────────────────────────────────────────────────

_FONTS_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"

_FONT_OLD_ENGLISH_FAMILY = "Old English"   # nome registrado no TTF
_FONT_ROBOTO_FAMILY      = "Roboto"

_fonts_loaded = False

def load_custom_fonts() -> None:
    """Registra as fontes customizadas na QFontDatabase. Chamar uma vez em main_app.py."""
    global _fonts_loaded
    if _fonts_loaded:
        return

    candidates = [
        (_FONTS_DIR / "old_english.ttf",  _FONT_OLD_ENGLISH_FAMILY),
        (_FONTS_DIR / "roboto.ttf",        _FONT_ROBOTO_FAMILY),
        # Variantes comuns de nome de arquivo
        (_FONTS_DIR / "OldEnglish.ttf",    _FONT_OLD_ENGLISH_FAMILY),
        (_FONTS_DIR / "Roboto-Regular.ttf", _FONT_ROBOTO_FAMILY),
    ]

    db = QFontDatabase()
    for path, _family in candidates:
        if path.exists():
            db.addApplicationFont(str(path))

    _fonts_loaded = True


def font_display(size: int = 14, bold: bool = False) -> QFont:
    """Old English — para marca, títulos de seção."""
    load_custom_fonts()
    f = QFont(_FONT_OLD_ENGLISH_FAMILY, size)
    f.setBold(bold)
    # Fallback gracioso se a fonte não carregar
    f.setStyleHint(QFont.Serif)
    return f


def font_ui(size: int = 9, bold: bool = False) -> QFont:
    """Roboto — para labels de UI, headers de tabela, badges."""
    load_custom_fonts()
    f = QFont(_FONT_ROBOTO_FAMILY, size)
    f.setBold(bold)
    f.setStyleHint(QFont.SansSerif)
    return f


def font_body(size: int = 13, bold: bool = False) -> QFont:
    """Roboto — para conteúdo de tabela, inputs, texto geral."""
    return font_ui(size, bold)


# ───────────────────────────────────────────────────────────────────
# TEMA ESCURO — "Frontline Intelligence"
# ───────────────────────────────────────────────────────────────────

class DarkColors:
    VOID       = "#0f1114"
    SHADOW     = "#141820"
    DEEP       = "#1a1f2a"
    PANEL      = "#1e2530"
    SURFACE    = "#242c3a"
    LIFTED     = "#2c3548"
    BORDER     = "#303848"
    MUTED      = "#3d4860"

    BRASS      = "#b8832a"
    AMBER      = "#d4a030"
    GOLD       = "#f0b840"
    GOLD_GLOW  = "rgba(208,160,48,0.12)"
    GOLD_SOFT  = "rgba(200,148,32,0.08)"

    TEXT_PRIMARY   = "#d8d0c0"
    TEXT_SECONDARY = "#a09080"
    TEXT_MUTED     = "#605850"
    TEXT_ACCENT    = "#e8c060"

    TAB_INACTIVE_TEXT = "#7a6858"
    TAB_HOVER_TEXT    = "#b0a090"

    SUCCESS     = "#2d6e3a"
    SUCCESS_TXT = "#7ec890"
    WARNING     = "#7a5818"
    WARNING_TXT = "#e8b860"
    DANGER      = "#6e2d2d"
    DANGER_TXT  = "#e88080"
    INFO        = "#2d4a6e"
    INFO_TXT    = "#80b0e8"


# ───────────────────────────────────────────────────────────────────
# TEMA CLARO — "Field Manual" (papel de briefing militar)
# ───────────────────────────────────────────────────────────────────

class LightColors:
    VOID       = "#f5f0e8"   # Pergaminho claro
    SHADOW     = "#ede8dc"   # Fundo de toolbar/status
    DEEP       = "#e8e0d0"   # Stats bar, campaign bar
    PANEL      = "#e2dace"   # Painéis principais
    SURFACE    = "#d8d0c0"   # Cards, células
    LIFTED     = "#cec4b2"   # Hover, elevados
    BORDER     = "#b8ac98"   # Bordas padrão
    MUTED      = "#9c8e7a"   # Bordas suaves

    BRASS      = "#7a4e18"   # Acento principal (mais escuro no claro)
    AMBER      = "#9a6420"   # Acento médio
    GOLD       = "#b87828"   # Acento vivo
    GOLD_GLOW  = "rgba(122,78,24,0.10)"
    GOLD_SOFT  = "rgba(122,78,24,0.06)"

    TEXT_PRIMARY   = "#1e1810"   # Tinta escura quente
    TEXT_SECONDARY = "#3a2e20"   # Texto secundário
    TEXT_MUTED     = "#7a6a54"   # Texto desativado
    TEXT_ACCENT    = "#8a5c10"   # Destaque

    TAB_INACTIVE_TEXT = "#5a4830"
    TAB_HOVER_TEXT    = "#3a2e20"

    SUCCESS     = "#c8ecd0"
    SUCCESS_TXT = "#1e5a2a"
    WARNING     = "#f0e0b0"
    WARNING_TXT = "#7a4e08"
    DANGER      = "#f0c8c8"
    DANGER_TXT  = "#7a1a1a"
    INFO        = "#c8daf0"
    INFO_TXT    = "#1a3a6a"


# ───────────────────────────────────────────────────────────────────
# ALIAS ATIVO — aponta para o tema atual
# ───────────────────────────────────────────────────────────────────

# Mude para LightColors para o tema claro
DSColors = DarkColors   # padrão: escuro


# ───────────────────────────────────────────────────────────────────
# ESTADOS
# ───────────────────────────────────────────────────────────────────

class DSStates:
    LOADING = "loading"
    EMPTY   = "empty"
    ERROR   = "error"
    SUCCESS = "success"


# ───────────────────────────────────────────────────────────────────
# ESPAÇAMENTO
# ───────────────────────────────────────────────────────────────────

class DSSpacing:
    ICON_PREVIEW_SIZE  = 160
    BORDER_RADIUS      = 2
    PADDING_SMALL      = 6
    PADDING_MEDIUM     = 12
    PADDING_LARGE      = 20
    TABLE_ROW_HEIGHT   = 36
    HEADER_HEIGHT      = 44
    TAB_HEIGHT         = 40
    FORM_LABEL_WIDTH   = 160   # largura fixa da coluna de labels no formulário
    FORM_MAX_WIDTH     = 680   # largura máxima dos campos de formulário
    PROFILE_PANEL_W    = 260   # largura do painel lateral de perfil
    PORTRAIT_W         = 200
    PORTRAIT_H         = 260


# ───────────────────────────────────────────────────────────────────
# FEEDBACK
# ───────────────────────────────────────────────────────────────────

class DSFeedback:
    TOAST_LEVEL_STYLES: dict = {
        "info": "",
        "warning": "",
        "error": "",
        "success": "",
    }
    LOADING_OVERLAY_BG  = ""
    LOADING_TITLE_TEXT  = ""
    LOADING_BAR_ACTIVE  = ""
    LOADING_BAR_IDLE    = ""

    @staticmethod
    def get_toast_style(level: str) -> str:
        """Returns theme-aware toast CSS for the given level. Reads DSColors at call time."""
        return DSFeedback.TOAST_LEVEL_STYLES.get(level, DSFeedback.TOAST_LEVEL_STYLES.get("info", ""))


# ───────────────────────────────────────────────────────────────────
# GERADOR DE QSS POR TEMA
# ───────────────────────────────────────────────────────────────────

def _svg_chevron(color: str) -> str:
    """Generates a chevron SVG as data URI for QSS image: url(...)."""
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
    """Gera uma classe DSStyles para um conjunto de cores C."""

    class _Styles:
        PANEL_PLACEHOLDER = (
            f"color:{C.TEXT_MUTED}; border:1px solid {C.BORDER}; background:{C.PANEL};"
        )
        PANEL_DASHED_PLACEHOLDER = (
            f"color:{C.TEXT_MUTED}; border:1px dashed {C.MUTED};"
        )

        # Banners de estado
        STATE_INFO = (
            f"color:{C.INFO_TXT}; background:{C.INFO}; "
            f"border-left:3px solid {C.INFO_TXT}; padding:6px 10px; border-radius:1px;"
        )
        STATE_SUCCESS = (
            f"color:{C.SUCCESS_TXT}; background:{C.SUCCESS}; "
            f"border-left:3px solid {C.SUCCESS_TXT}; padding:6px 10px; border-radius:1px;"
        )
        STATE_WARNING = (
            f"color:{C.WARNING_TXT}; background:{C.WARNING}; "
            f"border-left:3px solid {C.WARNING_TXT}; padding:6px 10px; border-radius:1px;"
        )
        STATE_ERROR = (
            f"color:{C.DANGER_TXT}; background:{C.DANGER}; "
            f"border-left:3px solid {C.DANGER_TXT}; padding:6px 10px; border-radius:1px;"
        )

        TABLE = f"""
            QTableWidget {{
                background: {C.VOID};
                color: {C.TEXT_SECONDARY};
                border: none;
                gridline-color: {C.BORDER};
                selection-background-color: {C.GOLD_GLOW};
            }}
            QTableWidget::item:selected {{
                color: {C.TEXT_PRIMARY};
                background: {C.GOLD_GLOW};
                border: none;
            }}
            QTableWidget::item:hover {{
                background: {C.GOLD_GLOW};
                color: {C.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background: {C.DEEP};
                color: {C.TEXT_MUTED};
                border: none;
                border-right: 1px solid {C.BORDER};
                border-bottom: 1px solid {C.BORDER};
                padding: 6px 12px;
                font-size: 9px;
                font-weight: 600;
                letter-spacing: 1.5px;
                text-transform: uppercase;
            }}
            QTableWidget::item {{
                padding: 6px 12px;
                border-bottom: 1px solid {C.BORDER};
            }}
        """

        TABLE_HIGH_CONTRAST = """
            QTableWidget {
                background: #080a0c; color: #f0ead8; border: none; gridline-color: #505060;
            }
            QHeaderView::section {
                background: #0f1218; color: #c0b8a0; border-bottom: 1px solid #505060; padding: 6px 12px;
            }
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
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QDateEdit:focus {{
                border-color: {C.BRASS};
            }}
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
            QComboBox:hover {{ border-color: {C.MUTED}; }}
            QComboBox:focus {{ border-color: {C.BRASS}; }}
            QComboBox:on {{ border-color: {C.BRASS}; background: {C.LIFTED}; }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 28px;
                border: none;
                border-left: 1px solid {C.BORDER};
                background: transparent;
            }}
            QComboBox::drop-down:hover {{ background: {C.GOLD_GLOW}; }}
            QComboBox::down-arrow {{ image: url("{_svg_chevron(C.TEXT_MUTED)}"); width: 12px; height: 12px; }}
            QComboBox::down-arrow:hover {{ image: url("{_svg_chevron(C.AMBER)}"); }}
            QComboBox::down-arrow:on {{ image: url("{_svg_chevron(C.GOLD)}"); }}
            QComboBox::down-arrow:disabled {{ image: url("{_svg_chevron(C.TEXT_MUTED)}"); opacity: 0.4; }}
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
            QComboBox QAbstractItemView::item {{ padding: 5px 12px; min-height: 26px; }}
            QComboBox QAbstractItemView::item:selected {{ background: {C.GOLD_GLOW}; color: {C.TEXT_PRIMARY}; }}
        """

        GROUP_BOX = f"""
            QGroupBox {{
                color: {C.AMBER};
                border: 1px solid {C.BORDER};
                border-top: 2px solid {C.BRASS};
                border-radius: 2px;
                margin-top: 14px;
                padding-top: 10px;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 1px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                left: 10px;
                color: {C.AMBER};
            }}
        """

        SCROLL = f"""
            QScrollBar:vertical {{
                background: {C.VOID}; width: 6px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {C.MUTED}; border-radius: 3px; min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {C.BRASS}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar:horizontal {{
                background: {C.VOID}; height: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background: {C.MUTED}; border-radius: 3px; min-width: 24px;
            }}
            QScrollBar::handle:horizontal:hover {{ background: {C.BRASS}; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
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
                border-bottom: 2px solid transparent;
                padding: 9px 18px;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.8px;
                min-width: 80px;
            }}
            QTabBar::tab:selected {{
                color: {C.AMBER};
                border-bottom: 2px solid {C.AMBER};
                background: {C.SHADOW};
            }}
            QTabBar::tab:hover:!selected {{
                color: {C.TAB_HOVER_TEXT};
                background: {C.DEEP};
            }}
            QTabBar::tab:first {{ margin-left: 8px; }}
        """

        TOOLBAR = f"""
            QToolBar {{
                background: {C.SHADOW};
                border-bottom: 1px solid {C.BRASS};
                spacing: 2px;
                padding: 2px 12px;
            }}
            QToolButton, QToolBar QPushButton {{
                background: transparent;
                color: {C.TEXT_SECONDARY};
                border: 1px solid transparent;
                border-radius: 2px;
                padding: 4px 12px;
                font-size: 9px;
                font-weight: 600;
                letter-spacing: 1px;
                min-height: 26px;
            }}
            QToolButton:hover, QToolBar QPushButton:hover {{
                color: {C.AMBER};
                border-color: {C.BRASS};
                background: {C.GOLD_GLOW};
            }}
            QToolButton:pressed {{ background: rgba(184,131,42,0.15); }}
            QToolButton:disabled {{ color: {C.TEXT_MUTED}; }}
        """

        STATUS_BAR = f"""
            QStatusBar {{
                background: {C.SHADOW};
                color: {C.TEXT_MUTED};
                border-top: 1px solid {C.BORDER};
                font-size: 10px;
                letter-spacing: 0.5px;
            }}
            QStatusBar::item {{ border: none; }}
        """

        MAIN_WINDOW = f"""
            QMainWindow {{ background: {C.VOID}; }}
            QMainWindow::separator {{ background: {C.BORDER}; width: 1px; height: 1px; }}
        """

        PROGRESS_BAR = f"""
            QProgressBar {{
                background: {C.BORDER};
                border: none;
                border-radius: 2px;
                text-align: center;
                font-size: 9px;
                color: transparent;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {C.BRASS}, stop:1 {C.GOLD});
                border-radius: 2px;
            }}
        """

        LABEL_ACCENT    = f"color:{C.AMBER}; font-weight:600; letter-spacing:1px;"
        LABEL_SECTION   = f"color:{C.BRASS}; font-weight:600; font-size:9px; letter-spacing:2px;"
        LABEL_VALUE_LARGE = f"color:{C.GOLD}; font-size:20px; font-weight:700;"
        LABEL_MUTED     = f"color:{C.TEXT_MUTED}; font-size:11px;"

    return _Styles


# Instâncias prontas
_DarkStyles  = _build_styles(DarkColors)
_LightStyles = _build_styles(LightColors)

# Alias ativo (começa no dark)
DSStyles = _DarkStyles


# ───────────────────────────────────────────────────────────────────
# THEME MANAGER — troca em runtime
# ───────────────────────────────────────────────────────────────────

_current_theme: str = "dark"


def current_theme() -> str:
    return _current_theme


def _refresh_feedback() -> None:
    """Rebuilds DSFeedback attributes using the current DSColors alias."""
    DSFeedback.TOAST_LEVEL_STYLES = {
        "info":    f"background:{DSColors.DEEP}; color:{DSColors.INFO_TXT}; border:1px solid {DSColors.INFO_TXT};",
        "warning": f"background:{DSColors.DEEP}; color:{DSColors.WARNING_TXT}; border:1px solid {DSColors.WARNING_TXT};",
        "error":   f"background:{DSColors.DEEP}; color:{DSColors.DANGER_TXT}; border:1px solid {DSColors.DANGER_TXT};",
        "success": f"background:{DSColors.DEEP}; color:{DSColors.SUCCESS_TXT}; border:1px solid {DSColors.SUCCESS_TXT};",
    }
    if _current_theme == "light":
        DSFeedback.LOADING_OVERLAY_BG  = "background-color: rgba(235,225,210,0.92);"
    else:
        DSFeedback.LOADING_OVERLAY_BG  = "background-color: rgba(10,12,14,0.88);"
    DSFeedback.LOADING_TITLE_TEXT  = f"color:{DSColors.AMBER}; font-weight:600; font-size:13px; letter-spacing:1px;"
    DSFeedback.LOADING_BAR_ACTIVE  = DSColors.AMBER
    DSFeedback.LOADING_BAR_IDLE    = DSColors.BORDER


def set_theme(theme: str) -> None:
    """
    Changes the active theme. theme: "dark" | "light"
    Updates DSColors, DSStyles and DSFeedback globally.
    Call QApplication.instance().setStyleSheet(build_global_stylesheet()) afterwards.
    """
    global _current_theme, DSColors, DSStyles

    _current_theme = theme
    if theme == "light":
        DSColors = LightColors
        DSStyles = _build_styles(LightColors)
    else:
        DSColors = DarkColors
        DSStyles = _build_styles(DarkColors)
    _refresh_feedback()


# ───────────────────────────────────────────────────────────────────
# GLOBAL STYLESHEET
# ───────────────────────────────────────────────────────────────────

def build_global_stylesheet() -> str:
    """Retorna QSS completo para QApplication.setStyleSheet(). Respeita o tema atual."""
    C = DSColors
    S = DSStyles
    return (
        S.MAIN_WINDOW
        + S.TOOLBAR
        + S.TAB_WIDGET
        + S.STATUS_BAR
        + S.TABLE
        + S.INPUT
        + S.COMBO
        + S.SCROLL
        + S.PROGRESS_BAR
        + S.GROUP_BOX
        + f"""
        QWidget {{
            background: {C.VOID};
            color: {C.TEXT_SECONDARY};
            font-family: "{_FONT_ROBOTO_FAMILY}", "Segoe UI", sans-serif;
            font-size: 13px;
        }}
        QLabel {{ background: transparent; color: {C.TEXT_SECONDARY}; }}
        QSplitter::handle {{ background: {C.BORDER}; width: 1px; height: 1px; }}
        QCheckBox {{ color: {C.TEXT_SECONDARY}; spacing: 6px; }}
        QCheckBox::indicator {{
            width: 14px; height: 14px;
            background: {C.SURFACE};
            border: 1px solid {C.BORDER};
            border-radius: 1px;
        }}
        QCheckBox::indicator:checked {{
            background: {C.BRASS}; border-color: {C.AMBER};
        }}
        QCheckBox:hover {{ color: {C.TEXT_PRIMARY}; }}
        QToolTip {{
            background: {C.PANEL}; color: {C.TEXT_PRIMARY};
            border: 1px solid {C.BRASS};
            padding: 4px 8px; border-radius: 2px; font-size: 11px;
        }}
        QMessageBox {{ background: {C.PANEL}; }}
        QMessageBox QLabel {{ color: {C.TEXT_PRIMARY}; }}
        QSplitter::handle:horizontal {{ background: {C.BORDER}; width: 1px; }}
        QSplitter::handle:vertical   {{ background: {C.BORDER}; height: 1px; }}
        QFormLayout QLabel {{
            color: {C.TEXT_SECONDARY};
            font-size: 12px;
            min-width: {DSSpacing.FORM_LABEL_WIDTH}px;
            max-width: {DSSpacing.FORM_LABEL_WIDTH}px;
        }}
        """
    )


# ───────────────────────────────────────────────────────────────────
# Helpers de botão
# ───────────────────────────────────────────────────────────────────

def apply_primary_button(button: QPushButton) -> None:
    C = DSColors
    button.setMinimumHeight(30)
    button.setFont(font_ui(10, bold=True))
    button.setStyleSheet(f"""
        QPushButton {{
            background: {C.BRASS}; color: {C.VOID};
            border: 1px solid {C.AMBER}; border-radius: 2px;
            padding: 6px 16px; font-weight: 700; font-size: 10px; letter-spacing: 1px;
        }}
        QPushButton:hover {{ background: {C.AMBER}; border-color: {C.GOLD}; }}
        QPushButton:pressed {{ background: {C.BRASS}; }}
        QPushButton:disabled {{
            background: {C.SURFACE}; color: {C.TEXT_MUTED}; border-color: {C.BORDER};
        }}
    """)


def apply_ghost_button(button: QPushButton) -> None:
    C = DSColors
    button.setMinimumHeight(28)
    button.setFont(font_ui(10))
    button.setStyleSheet(f"""
        QPushButton {{
            background: transparent; color: {C.TEXT_SECONDARY};
            border: 1px solid {C.BORDER}; border-radius: 2px;
            padding: 5px 12px; font-size: 10px; letter-spacing: 1px;
        }}
        QPushButton:hover {{ color: {C.AMBER}; border-color: {C.BRASS}; background: {C.GOLD_GLOW}; }}
        QPushButton:pressed {{ background: rgba(184,131,42,0.15); }}
        QPushButton:disabled {{ color: {C.TEXT_MUTED}; border-color: {C.BORDER}; }}
    """)


def apply_danger_button(button: QPushButton) -> None:
    C = DSColors
    button.setMinimumHeight(28)
    button.setStyleSheet(f"""
        QPushButton {{
            background: transparent; color: {C.DANGER_TXT};
            border: 1px solid {C.DANGER}; border-radius: 2px; padding: 5px 12px;
        }}
        QPushButton:hover {{ background: rgba(110,45,45,0.20); border-color: {C.DANGER_TXT}; }}
    """)


def apply_section_group(group: QGroupBox) -> None:
    group.setFlat(False)
    group.setFont(font_ui(10, bold=True))
    group.setStyleSheet(DSStyles.GROUP_BOX)


# Initialize DSFeedback with dark-theme defaults at module load
_refresh_feedback()
