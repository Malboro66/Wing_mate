# -*- coding: utf-8 -*-
# tests/test_tab_contrast_wcag.py
# Testes de contraste WCAG 2.1 AA para QTabBar do Wing Mate

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from tests.utils.wcag import contrast_ratio, passes_aa_normal, passes_aa_large
from app.ui.design_system import DarkColors as D, LightColors as L


# ── Tema escuro ──────────────────────────────────────────────────────────────

class TestDarkThemeTabContrast:
    """Verifica contraste dos tokens de cor das abas no tema escuro."""

    def test_active_tab_text_passes_aa_normal(self):
        """Aba ativa: AMBER sobre SHADOW deve ter >= 4.5:1."""
        ratio = contrast_ratio(D.AMBER, D.SHADOW)
        assert passes_aa_normal(D.AMBER, D.SHADOW), (
            f"Tab ativa (escura) falhou AA normal: {ratio:.2f}:1 "
            f"(texto={D.AMBER}, bg={D.SHADOW})"
        )

    def test_active_tab_text_passes_aaa_normal(self):
        """Aba ativa deve idealmente passar AAA (>= 7.0:1) para máxima legibilidade."""
        ratio = contrast_ratio(D.AMBER, D.SHADOW)
        assert ratio >= 7.0, (
            f"Tab ativa (escura) não atingiu AAA: {ratio:.2f}:1 "
            f"(texto={D.AMBER}, bg={D.SHADOW})"
        )

    def test_active_tab_underline_passes_aa_component(self):
        """O underline de 3px é componente de UI: mínimo 3.0:1."""
        ratio = contrast_ratio(D.AMBER, D.SHADOW)
        assert passes_aa_large(D.AMBER, D.SHADOW), (
            f"Underline de tab ativa (escura) falhou AA componente: {ratio:.2f}:1"
        )

    def test_inactive_tab_text_passes_aa_normal(self):
        """Aba inativa: TAB_INACTIVE_TEXT sobre SHADOW deve ter >= 4.5:1."""
        ratio = contrast_ratio(D.TAB_INACTIVE_TEXT, D.SHADOW)
        assert passes_aa_normal(D.TAB_INACTIVE_TEXT, D.SHADOW), (
            f"Tab inativa (escura) falhou AA normal: {ratio:.2f}:1 "
            f"(texto={D.TAB_INACTIVE_TEXT}, bg={D.SHADOW})"
        )

    def test_inactive_tab_hover_text_passes_aa_normal(self):
        """Aba inativa em hover: TAB_HOVER_TEXT sobre SHADOW deve ter >= 4.5:1."""
        ratio = contrast_ratio(D.TAB_HOVER_TEXT, D.SHADOW)
        assert passes_aa_normal(D.TAB_HOVER_TEXT, D.SHADOW), (
            f"Tab inativa hover (escura) falhou AA normal: {ratio:.2f}:1 "
            f"(texto={D.TAB_HOVER_TEXT}, bg={D.SHADOW})"
        )

    def test_active_tab_underline_is_visually_distinct_from_inactive(self):
        """O indicador ativo deve ter contraste >= 3.0:1 contra o fundo da barra."""
        ratio = contrast_ratio(D.AMBER, D.SHADOW)
        assert ratio >= 3.0, (
            f"Underline ativo não se distingue do fundo da barra: {ratio:.2f}:1"
        )


# ── Tema claro ───────────────────────────────────────────────────────────────

class TestLightThemeTabContrast:
    """Verifica contraste dos tokens de cor das abas no tema claro."""

    def test_active_tab_text_passes_aa_normal(self):
        """Aba ativa (claro): AMBER sobre SHADOW deve ter >= 4.5:1."""
        ratio = contrast_ratio(L.AMBER, L.SHADOW)
        assert passes_aa_normal(L.AMBER, L.SHADOW), (
            f"Tab ativa (clara) falhou AA normal: {ratio:.2f}:1 "
            f"(texto={L.AMBER}, bg={L.SHADOW})"
        )

    def test_inactive_tab_text_passes_aa_normal(self):
        """Aba inativa (claro): TAB_INACTIVE_TEXT sobre SHADOW deve ter >= 4.5:1."""
        ratio = contrast_ratio(L.TAB_INACTIVE_TEXT, L.SHADOW)
        assert passes_aa_normal(L.TAB_INACTIVE_TEXT, L.SHADOW), (
            f"Tab inativa (clara) falhou AA normal: {ratio:.2f}:1 "
            f"(texto={L.TAB_INACTIVE_TEXT}, bg={L.SHADOW})"
        )

    def test_inactive_tab_hover_text_passes_aa_normal(self):
        """Aba inativa hover (claro): TAB_HOVER_TEXT sobre SHADOW deve ter >= 4.5:1."""
        ratio = contrast_ratio(L.TAB_HOVER_TEXT, L.SHADOW)
        assert passes_aa_normal(L.TAB_HOVER_TEXT, L.SHADOW), (
            f"Tab inativa hover (clara) falhou AA normal: {ratio:.2f}:1 "
            f"(texto={L.TAB_HOVER_TEXT}, bg={L.SHADOW})"
        )

    def test_active_underline_passes_aa_component(self):
        """Underline ativo (claro): mínimo 3.0:1."""
        ratio = contrast_ratio(L.AMBER, L.SHADOW)
        assert passes_aa_large(L.AMBER, L.SHADOW), (
            f"Underline de tab ativa (clara) falhou AA componente: {ratio:.2f}:1"
        )


# ── Verificação cruzada dos tokens novos ─────────────────────────────────────

class TestTabTokensExist:
    """Garante que os novos tokens TAB_INACTIVE_TEXT e TAB_HOVER_TEXT existem."""

    def test_dark_colors_has_tab_inactive_text(self):
        assert hasattr(D, "TAB_INACTIVE_TEXT"), (
            "DarkColors não possui atributo TAB_INACTIVE_TEXT"
        )

    def test_dark_colors_has_tab_hover_text(self):
        assert hasattr(D, "TAB_HOVER_TEXT"), (
            "DarkColors não possui atributo TAB_HOVER_TEXT"
        )

    def test_light_colors_has_tab_inactive_text(self):
        assert hasattr(L, "TAB_INACTIVE_TEXT"), (
            "LightColors não possui atributo TAB_INACTIVE_TEXT"
        )

    def test_light_colors_has_tab_hover_text(self):
        assert hasattr(L, "TAB_HOVER_TEXT"), (
            "LightColors não possui atributo TAB_HOVER_TEXT"
        )

    def test_dark_tab_inactive_text_is_valid_hex(self):
        val = D.TAB_INACTIVE_TEXT
        assert val.startswith("#") and len(val) in (4, 7), (
            f"TAB_INACTIVE_TEXT inválido: {val!r}"
        )

    def test_light_tab_inactive_text_is_valid_hex(self):
        val = L.TAB_INACTIVE_TEXT
        assert val.startswith("#") and len(val) in (4, 7), (
            f"TAB_INACTIVE_TEXT inválido: {val!r}"
        )
