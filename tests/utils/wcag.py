# -*- coding: utf-8 -*-
# tests/utils/wcag.py
# Utilitários de cálculo de contraste WCAG 2.1

from __future__ import annotations


def _linearize(c: float) -> float:
    """Converte canal sRGB normalizado (0–1) para espaço linear."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    """
    Calcula a luminância relativa WCAG de uma cor hexadecimal.

    Args:
        hex_color: Cor no formato '#rrggbb' ou '#rgb'

    Returns:
        Luminância relativa entre 0.0 (preto) e 1.0 (branco)
    """
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (
        0.2126 * _linearize(r)
        + 0.7152 * _linearize(g)
        + 0.0722 * _linearize(b)
    )


def contrast_ratio(fg: str, bg: str) -> float:
    """
    Retorna a razão de contraste WCAG entre duas cores.

    Args:
        fg: Cor do primeiro plano (texto) em '#rrggbb'
        bg: Cor do fundo em '#rrggbb'

    Returns:
        Razão de contraste entre 1.0 e 21.0
    """
    l1 = relative_luminance(fg)
    l2 = relative_luminance(bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def passes_aa_normal(fg: str, bg: str) -> bool:
    """Texto normal (< 18pt não-bold, < 14pt bold): mínimo 4.5:1."""
    return contrast_ratio(fg, bg) >= 4.5


def passes_aa_large(fg: str, bg: str) -> bool:
    """
    Texto grande (≥ 18pt ou ≥ 14pt bold) ou componente de UI: mínimo 3.0:1.

    Usar para: bordas de input focado, indicadores de estado, underlines de tab.
    """
    return contrast_ratio(fg, bg) >= 3.0


def passes_aaa_normal(fg: str, bg: str) -> bool:
    """Critério AAA para texto normal: mínimo 7.0:1."""
    return contrast_ratio(fg, bg) >= 7.0
