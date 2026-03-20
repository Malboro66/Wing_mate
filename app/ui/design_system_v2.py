# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - app/ui/design_system.py
# Design System v2 — "Frontline Intelligence" Aesthetic
#
# Paleta: Charcoal profundo + acentos âmbar/latão
# Tipografia: Courier/monospace + Oswald (UI labels)
# Linguagem visual: briefing room militar WWI
# ===================================================================

from __future__ import annotations

from PyQt5.QtWidgets import QGroupBox, QPushButton


# ───────────────────────────────────────────────────────────────────
# CORES BASE
# ───────────────────────────────────────────────────────────────────

class DSColors:
    # Camadas de fundo (do mais escuro ao mais claro)
    VOID       = "#0f1114"   # Fundo absoluto
    SHADOW     = "#141820"   # Barra de status, toolbar
    DEEP       = "#1a1f2a"   # Stats bar, campaign bar
    PANEL      = "#1e2530"   # Painéis principais
    SURFACE    = "#242c3a"   # Cards, células de tabela
    LIFTED     = "#2c3548"   # Hover, elementos elevados
    BORDER     = "#303848"   # Bordas padrão
    MUTED      = "#3d4860"   # Bordas suaves, separadores

    # Acentos — Latão & Âmbar (militar, histórico)
    BRASS      = "#b8832a"   # Acento principal (bordas ativas, indicadores)
    AMBER      = "#d4a030"   # Acento médio (labels, títulos de seção)
    GOLD       = "#f0b840"   # Acento vivo (valores, highlights)
    GOLD_GLOW  = "rgba(208,160,48,0.12)"   # Background de hover/seleção
    GOLD_SOFT  = "rgba(200,148,32,0.08)"   # Background muito suave

    # Texto
    TEXT_PRIMARY   = "#d8d0c0"  # Texto principal (quente, não branco puro)
    TEXT_SECONDARY = "#a09080"  # Texto secundário
    TEXT_MUTED     = "#605850"  # Texto desativado / placeholder
    TEXT_ACCENT    = "#e8c060"  # Texto de destaque

    # Semânticos
    SUCCESS     = "#2d6e3a"   # Fundo success
    SUCCESS_TXT = "#7ec890"   # Texto success
    WARNING     = "#7a5818"   # Fundo warning
    WARNING_TXT = "#e8b860"   # Texto warning
    DANGER      = "#6e2d2d"   # Fundo danger
    DANGER_TXT  = "#e88080"   # Texto danger
    INFO        = "#2d4a6e"   # Fundo info
    INFO_TXT    = "#80b0e8"   # Texto info


# ───────────────────────────────────────────────────────────────────
# ESTILOS QSS
# ───────────────────────────────────────────────────────────────────

class DSStyles:
    """Strings de stylesheet para uso em setStyleSheet()."""

    # ── Placeholders ───────────────────────────────────────────────
    PANEL_PLACEHOLDER = (
        f"color:{DSColors.TEXT_MUTED}; "
        f"border:1px solid {DSColors.BORDER}; "
        f"background:{DSColors.PANEL};"
    )
    PANEL_DASHED_PLACEHOLDER = (
        f"color:{DSColors.TEXT_MUTED}; border:1px dashed {DSColors.MUTED};"
    )

    # ── Banners de estado ──────────────────────────────────────────
    STATE_INFO = (
        f"color:{DSColors.INFO_TXT}; "
        f"background:rgba(45,74,110,0.20); "
        f"border-left:3px solid {DSColors.INFO_TXT}; "
        f"padding:6px 10px; border-radius:1px;"
    )
    STATE_SUCCESS = (
        f"color:{DSColors.SUCCESS_TXT}; "
        f"background:rgba(45,110,58,0.20); "
        f"border-left:3px solid {DSColors.SUCCESS_TXT}; "
        f"padding:6px 10px; border-radius:1px;"
    )
    STATE_WARNING = (
        f"color:{DSColors.WARNING_TXT}; "
        f"background:rgba(122,88,24,0.20); "
        f"border-left:3px solid {DSColors.WARNING_TXT}; "
        f"padding:6px 10px; border-radius:1px;"
    )
    STATE_ERROR = (
        f"color:{DSColors.DANGER_TXT}; "
        f"background:rgba(110,45,45,0.20); "
        f"border-left:3px solid {DSColors.DANGER_TXT}; "
        f"padding:6px 10px; border-radius:1px;"
    )

    # ── Tabelas ────────────────────────────────────────────────────
    TABLE = f"""
        QTableWidget {{
            background: {DSColors.VOID};
            color: {DSColors.TEXT_SECONDARY};
            border: none;
            gridline-color: {DSColors.BORDER};
            selection-background-color: {DSColors.GOLD_GLOW};
        }}
        QTableWidget::item:selected {{
            color: {DSColors.TEXT_PRIMARY};
            background: rgba(184,131,42,0.10);
            border: none;
        }}
        QTableWidget::item:hover {{
            background: {DSColors.GOLD_GLOW};
            color: {DSColors.TEXT_PRIMARY};
        }}
        QHeaderView::section {{
            background: {DSColors.DEEP};
            color: {DSColors.TEXT_MUTED};
            border: none;
            border-right: 1px solid {DSColors.BORDER};
            border-bottom: 1px solid {DSColors.BORDER};
            padding: 6px 12px;
            font-size: 9px;
            font-weight: 600;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }}
        QTableWidget::item {{
            padding: 6px 12px;
            border-bottom: 1px solid {DSColors.BORDER};
        }}
    """

    TABLE_HIGH_CONTRAST = f"""
        QTableWidget {{
            background: #080a0c;
            color: #f0ead8;
            border: none;
            gridline-color: #505060;
        }}
        QHeaderView::section {{
            background: #0f1218;
            color: #c0b8a0;
            border-bottom: 1px solid #505060;
            padding: 6px 12px;
        }}
    """

    # ── Inputs ─────────────────────────────────────────────────────
    INPUT = f"""
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background: {DSColors.SURFACE};
            color: {DSColors.TEXT_PRIMARY};
            border: 1px solid {DSColors.BORDER};
            border-radius: 2px;
            padding: 5px 10px;
            selection-background-color: rgba(184,131,42,0.25);
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {DSColors.BRASS};
        }}
        QLineEdit::placeholder, QTextEdit::placeholder {{
            color: {DSColors.TEXT_MUTED};
        }}
    """

    # ── ComboBox ───────────────────────────────────────────────────
    COMBO = f"""
        QComboBox {{
            background: {DSColors.SURFACE};
            color: {DSColors.TEXT_PRIMARY};
            border: 1px solid {DSColors.BORDER};
            border-radius: 2px;
            padding: 4px 10px;
        }}
        QComboBox:focus {{ border-color: {DSColors.BRASS}; }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox QAbstractItemView {{
            background: {DSColors.PANEL};
            color: {DSColors.TEXT_SECONDARY};
            border: 1px solid {DSColors.BRASS};
            selection-background-color: {DSColors.GOLD_GLOW};
            selection-color: {DSColors.TEXT_PRIMARY};
            outline: none;
        }}
    """

    # ── GroupBox / Seção ───────────────────────────────────────────
    GROUP_BOX = f"""
        QGroupBox {{
            color: {DSColors.AMBER};
            border: 1px solid {DSColors.BORDER};
            border-top: 2px solid {DSColors.BRASS};
            border-radius: 2px;
            margin-top: 14px;
            padding-top: 12px;
            font-weight: 600;
            letter-spacing: 1px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            left: 12px;
            color: {DSColors.AMBER};
        }}
    """

    # ── ScrollArea ─────────────────────────────────────────────────
    SCROLL = f"""
        QScrollBar:vertical {{
            background: {DSColors.VOID};
            width: 6px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {DSColors.MUTED};
            border-radius: 3px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {DSColors.BRASS}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{
            background: {DSColors.VOID};
            height: 6px;
        }}
        QScrollBar::handle:horizontal {{
            background: {DSColors.MUTED};
            border-radius: 3px;
        }}
        QScrollBar::handle:horizontal:hover {{ background: {DSColors.BRASS}; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    """

    # ── TabWidget ──────────────────────────────────────────────────
    TAB_WIDGET = f"""
        QTabWidget::pane {{
            border: none;
            background: {DSColors.VOID};
        }}
        QTabBar::tab {{
            background: {DSColors.SHADOW};
            color: {DSColors.TEXT_MUTED};
            border: none;
            border-bottom: 2px solid transparent;
            padding: 9px 16px;
            font-size: 9px;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}
        QTabBar::tab:selected {{
            color: {DSColors.AMBER};
            border-bottom: 2px solid {DSColors.AMBER};
            background: {DSColors.SHADOW};
        }}
        QTabBar::tab:hover:!selected {{
            color: {DSColors.TEXT_SECONDARY};
            background: {DSColors.DEEP};
        }}
        QTabBar::tab:first {{ margin-left: 16px; }}
    """

    # ── ToolBar ────────────────────────────────────────────────────
    TOOLBAR = f"""
        QToolBar {{
            background: {DSColors.SHADOW};
            border-bottom: 1px solid {DSColors.BRASS};
            spacing: 2px;
            padding: 2px 12px;
        }}
        QToolButton, QToolBar QPushButton {{
            background: transparent;
            color: {DSColors.TEXT_SECONDARY};
            border: 1px solid transparent;
            border-radius: 2px;
            padding: 4px 10px;
            font-size: 9px;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}
        QToolButton:hover, QToolBar QPushButton:hover {{
            color: {DSColors.AMBER};
            border-color: {DSColors.BRASS};
            background: {DSColors.GOLD_GLOW};
        }}
        QToolButton:pressed, QToolBar QPushButton:pressed {{
            background: rgba(184,131,42,0.15);
        }}
        QToolButton:disabled {{
            color: {DSColors.TEXT_MUTED};
        }}
    """

    # ── StatusBar ──────────────────────────────────────────────────
    STATUS_BAR = f"""
        QStatusBar {{
            background: {DSColors.SHADOW};
            color: {DSColors.TEXT_MUTED};
            border-top: 1px solid {DSColors.BORDER};
            font-size: 10px;
            letter-spacing: 0.5px;
        }}
        QStatusBar::item {{ border: none; }}
    """

    # ── MainWindow ─────────────────────────────────────────────────
    MAIN_WINDOW = f"""
        QMainWindow {{
            background: {DSColors.VOID};
        }}
        QMainWindow::separator {{
            background: {DSColors.BORDER};
            width: 1px;
            height: 1px;
        }}
    """

    # ── ProgressBar ────────────────────────────────────────────────
    PROGRESS_BAR = f"""
        QProgressBar {{
            background: {DSColors.BORDER};
            border: none;
            border-radius: 2px;
            height: 4px;
            text-align: center;
            font-size: 9px;
            color: transparent;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {DSColors.BRASS},
                stop:1 {DSColors.GOLD}
            );
            border-radius: 2px;
        }}
    """

    # ── Label de destaque ──────────────────────────────────────────
    LABEL_ACCENT = f"color:{DSColors.AMBER}; font-weight:600; letter-spacing:1px;"
    LABEL_SECTION = f"color:{DSColors.BRASS}; font-weight:600; font-size:9px; letter-spacing:2px; text-transform:uppercase;"
    LABEL_VALUE_LARGE = f"color:{DSColors.GOLD}; font-size:20px; font-weight:700;"
    LABEL_MUTED = f"color:{DSColors.TEXT_MUTED}; font-size:11px;"


# ───────────────────────────────────────────────────────────────────
# FEEDBACK
# ───────────────────────────────────────────────────────────────────

class DSFeedback:
    """Tokens de design para componentes de feedback operacional."""

    TOAST_LEVEL_STYLES = {
        "info":    f"background:{DSColors.DEEP}; color:{DSColors.INFO_TXT}; border:1px solid {DSColors.INFO_TXT};",
        "warning": f"background:{DSColors.DEEP}; color:{DSColors.WARNING_TXT}; border:1px solid {DSColors.WARNING_TXT};",
        "error":   f"background:{DSColors.DEEP}; color:{DSColors.DANGER_TXT}; border:1px solid {DSColors.DANGER_TXT};",
        "success": f"background:{DSColors.DEEP}; color:{DSColors.SUCCESS_TXT}; border:1px solid {DSColors.SUCCESS_TXT};",
    }

    LOADING_OVERLAY_BG   = f"background-color: rgba(10,12,14,0.88);"
    LOADING_TITLE_TEXT   = f"color:{DSColors.AMBER}; font-weight:600; font-size:13px; letter-spacing:1px;"
    LOADING_BAR_ACTIVE   = DSColors.AMBER
    LOADING_BAR_IDLE     = DSColors.BORDER


# ───────────────────────────────────────────────────────────────────
# ESPAÇAMENTO
# ───────────────────────────────────────────────────────────────────

class DSSpacing:
    ICON_PREVIEW_SIZE = 160
    BORDER_RADIUS     = 2     # px — bordas quadradas, linguagem militar
    PADDING_SMALL     = 6
    PADDING_MEDIUM    = 12
    PADDING_LARGE     = 20
    TABLE_ROW_HEIGHT  = 36    # px
    HEADER_HEIGHT     = 44    # toolbar
    TAB_HEIGHT        = 40


# ───────────────────────────────────────────────────────────────────
# ESTADOS
# ───────────────────────────────────────────────────────────────────

class DSStates:
    LOADING = "loading"
    EMPTY   = "empty"
    ERROR   = "error"
    SUCCESS = "success"


# ───────────────────────────────────────────────────────────────────
# HELPERS DE APLICAÇÃO DE ESTILO
# ───────────────────────────────────────────────────────────────────

def apply_primary_button(button: QPushButton) -> None:
    """Botão de ação primária — âmbar/latão sobre escuro."""
    button.setMinimumHeight(30)
    button.setStyleSheet(f"""
        QPushButton {{
            background: {DSColors.BRASS};
            color: {DSColors.VOID};
            border: 1px solid {DSColors.AMBER};
            border-radius: {DSSpacing.BORDER_RADIUS}px;
            padding: 6px 16px;
            font-weight: 700;
            font-size: 10px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}
        QPushButton:hover {{
            background: {DSColors.AMBER};
            border-color: {DSColors.GOLD};
        }}
        QPushButton:pressed {{
            background: {DSColors.BRASS};
        }}
        QPushButton:disabled {{
            background: {DSColors.SURFACE};
            color: {DSColors.TEXT_MUTED};
            border-color: {DSColors.BORDER};
        }}
    """)


def apply_ghost_button(button: QPushButton) -> None:
    """Botão secundário — transparente com borda."""
    button.setMinimumHeight(28)
    button.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            color: {DSColors.TEXT_SECONDARY};
            border: 1px solid {DSColors.BORDER};
            border-radius: {DSSpacing.BORDER_RADIUS}px;
            padding: 5px 12px;
            font-size: 10px;
            letter-spacing: 1px;
        }}
        QPushButton:hover {{
            color: {DSColors.AMBER};
            border-color: {DSColors.BRASS};
            background: {DSColors.GOLD_GLOW};
        }}
        QPushButton:pressed {{
            background: rgba(184,131,42,0.15);
        }}
        QPushButton:disabled {{
            color: {DSColors.TEXT_MUTED};
            border-color: {DSColors.BORDER};
        }}
    """)


def apply_danger_button(button: QPushButton) -> None:
    """Botão destrutivo."""
    button.setMinimumHeight(28)
    button.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            color: {DSColors.DANGER_TXT};
            border: 1px solid {DSColors.DANGER};
            border-radius: {DSSpacing.BORDER_RADIUS}px;
            padding: 5px 12px;
            font-size: 10px;
        }}
        QPushButton:hover {{
            background: rgba(110,45,45,0.20);
            border-color: {DSColors.DANGER_TXT};
        }}
    """)


def apply_section_group(group: QGroupBox) -> None:
    """GroupBox com borda superior âmbar."""
    group.setFlat(False)
    group.setStyleSheet(DSStyles.GROUP_BOX)


# ───────────────────────────────────────────────────────────────────
# STYLESHEET GLOBAL
# Aplique em QApplication.instance().setStyleSheet(build_global_stylesheet())
# ───────────────────────────────────────────────────────────────────

def build_global_stylesheet() -> str:
    """Retorna stylesheet completo para aplicar na QApplication."""
    return (
        DSStyles.MAIN_WINDOW
        + DSStyles.TOOLBAR
        + DSStyles.TAB_WIDGET
        + DSStyles.STATUS_BAR
        + DSStyles.TABLE
        + DSStyles.INPUT
        + DSStyles.COMBO
        + DSStyles.SCROLL
        + DSStyles.PROGRESS_BAR
        + DSStyles.GROUP_BOX
        + f"""
        QWidget {{
            background: {DSColors.VOID};
            color: {DSColors.TEXT_SECONDARY};
            font-size: 13px;
        }}
        QLabel {{
            background: transparent;
            color: {DSColors.TEXT_SECONDARY};
        }}
        QSplitter::handle {{
            background: {DSColors.BORDER};
            width: 1px;
            height: 1px;
        }}
        QCheckBox {{
            color: {DSColors.TEXT_SECONDARY};
            spacing: 6px;
        }}
        QCheckBox::indicator {{
            width: 14px;
            height: 14px;
            background: {DSColors.SURFACE};
            border: 1px solid {DSColors.BORDER};
            border-radius: 1px;
        }}
        QCheckBox::indicator:checked {{
            background: {DSColors.BRASS};
            border-color: {DSColors.AMBER};
        }}
        QCheckBox:hover {{ color: {DSColors.TEXT_PRIMARY}; }}
        QToolTip {{
            background: {DSColors.PANEL};
            color: {DSColors.TEXT_PRIMARY};
            border: 1px solid {DSColors.BRASS};
            padding: 4px 8px;
            border-radius: 2px;
            font-size: 11px;
        }}
        QMessageBox {{
            background: {DSColors.PANEL};
        }}
        QMessageBox QLabel {{
            color: {DSColors.TEXT_PRIMARY};
        }}
        QFileDialog {{
            background: {DSColors.PANEL};
            color: {DSColors.TEXT_PRIMARY};
        }}
        """
    )
