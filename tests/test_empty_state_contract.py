# -*- coding: utf-8 -*-
# tests/test_empty_state_contract.py
# Testes de contrato para EmptyStateWidget e integração com QStackedWidget.

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

pytest.importorskip("pytestqt")

from PyQt5.QtWidgets import QStackedWidget
from pytestqt.qtbot import QtBot

from app.ui.widgets.empty_state import EmptyStateWidget


def test_empty_state_widget_renders_without_error(qtbot: QtBot) -> None:
    """EmptyStateWidget cria sem exceção com todos os parâmetros."""
    widget = EmptyStateWidget(
        icon="✈",
        title="Nenhuma missão carregada",
        body="Selecione uma campanha e sincronize.",
        cta_label="Sincronizar agora",
    )
    qtbot.addWidget(widget)
    widget.show()
    assert widget.isVisible()


def test_empty_state_widget_without_cta(qtbot: QtBot) -> None:
    """EmptyStateWidget sem cta_label não cria botão."""
    widget = EmptyStateWidget(
        icon="★",
        title="Sem ases",
        body="Dados aparecerão após sincronização.",
    )
    qtbot.addWidget(widget)
    assert widget._btn is None


def test_empty_state_widget_with_cta_emits_signal(qtbot: QtBot) -> None:
    """Clique no CTA emite action_triggered."""
    widget = EmptyStateWidget(
        icon="✈",
        title="Título",
        body="Corpo.",
        cta_label="Ação",
    )
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.action_triggered, timeout=1000):
        widget._btn.click()


def test_stacked_wrapper_starts_at_index_zero(qtbot: QtBot) -> None:
    """O QStackedWidget criado pelo wrapper começa no índice 0 (estado vazio)."""
    from PyQt5.QtWidgets import QWidget
    from app.ui.main_window import _make_tab_wrapper

    content = QWidget()
    empty = EmptyStateWidget("✈", "Vazio", "Corpo.")
    wrapper, stack = _make_tab_wrapper(content, empty)

    qtbot.addWidget(wrapper)
    assert stack.currentIndex() == 0
    assert stack.currentWidget() is empty


def test_stacked_wrapper_switches_to_content_on_index_one(qtbot: QtBot) -> None:
    """Definir índice 1 exibe o widget de conteúdo real."""
    from PyQt5.QtWidgets import QWidget
    from app.ui.main_window import _make_tab_wrapper

    content = QWidget()
    empty = EmptyStateWidget("✈", "Vazio", "Corpo.")
    wrapper, stack = _make_tab_wrapper(content, empty)

    qtbot.addWidget(wrapper)
    stack.setCurrentIndex(1)

    assert stack.currentIndex() == 1
    assert stack.currentWidget() is content


def test_empty_state_set_texts_updates_labels(qtbot: QtBot) -> None:
    """set_texts atualiza título e corpo sem recriar o widget."""
    widget = EmptyStateWidget(
        icon="✈",
        title="Título original",
        body="Corpo original.",
        cta_label="Ação",
    )
    qtbot.addWidget(widget)

    widget.set_texts("Título novo", "Corpo novo.", "Nova ação")

    layout = widget.layout()
    title_widget = layout.itemAt(1).widget() if layout.count() > 1 else None
    body_widget  = layout.itemAt(2).widget() if layout.count() > 2 else None

    assert title_widget is not None and title_widget.text() == "Título novo"
    assert body_widget  is not None and body_widget.text()  == "Corpo novo."
    assert widget._btn  is not None and widget._btn.text()  == "Nova ação"


def test_make_tab_wrapper_is_importable_from_main_window() -> None:
    """_make_tab_wrapper deve ser importável do módulo main_window."""
    from app.ui.main_window import _make_tab_wrapper
    assert callable(_make_tab_wrapper)
