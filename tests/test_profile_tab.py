# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - tests/test_profile_tab.py
# Testes unitários para a aba de perfil do piloto
# ===================================================================

import sys
from pathlib import Path
from datetime import datetime

# Adiciona diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from pytestqt.qtbot import QtBot
from PyQt5.QtCore import QDate

from app.ui.profile_tab import ProfileTab


def test_age_calculation(qtbot: QtBot):
    """Testa cálculo de idade com data de referência."""
    tab = ProfileTab()
    qtbot.addWidget(tab)
    
    # Define data de nascimento: 15/05/1890
    tab.dob_edit.setDate(QDate(1890, 5, 15))
    
    # Define data de referência: 01/10/1918
    tab.update_reference_date(datetime(1918, 10, 1))
    
    # Verifica idade calculada
    assert tab.age_label.text() == '28', f"Esperado '28', obtido '{tab.age_label.text()}'"


def test_validation_future_date(qtbot: QtBot):
    """Testa validação de data futura."""
    tab = ProfileTab()
    qtbot.addWidget(tab)
    
    # Define data futura
    tab.dob_edit.setDate(QDate(2030, 1, 1))
    
    # Valida
    valid, msg = tab._validate_profile()
    
    assert not valid, "Data futura deveria ser inválida"
    assert 'futura' in msg.lower(), f"Mensagem deveria mencionar 'futura': {msg}"


def test_birthplace_length_validation(qtbot: QtBot):
    """Testa validação de comprimento do local de nascimento."""
    tab = ProfileTab()
    qtbot.addWidget(tab)
    
    # Define data válida
    tab.dob_edit.setDate(QDate(1890, 1, 1))
    
    # Texto muito longo (> MAX_BIRTHPLACE)
    long_text = "A" * (tab.MAX_BIRTHPLACE + 10)
    tab.birthplace_edit.setText(long_text)
    
    valid, msg = tab._validate_profile()
    
    assert not valid, "Local de nascimento longo demais deveria ser inválido"
    assert 'caracteres' in msg.lower(), f"Mensagem deveria mencionar 'caracteres': {msg}"


def test_bio_length_validation(qtbot: QtBot):
    """Testa validação de comprimento da biografia."""
    tab = ProfileTab()
    qtbot.addWidget(tab)
    
    # Define data válida
    tab.dob_edit.setDate(QDate(1890, 1, 1))
    
    # Biografia muito longa (> MAX_BIO)
    long_bio = "B" * (tab.MAX_BIO + 10)
    tab.bio_edit.setPlainText(long_bio)
    
    valid, msg = tab._validate_profile()
    
    assert not valid, "Biografia longa demais deveria ser inválida"
    assert 'biografia' in msg.lower(), f"Mensagem deveria mencionar 'biografia': {msg}"


def test_valid_profile(qtbot: QtBot):
    """Testa validação de perfil válido."""
    tab = ProfileTab()
    qtbot.addWidget(tab)
    
    # Define dados válidos
    tab.dob_edit.setDate(QDate(1890, 5, 15))
    tab.birthplace_edit.setText("Berlin, Germany")
    tab.bio_edit.setPlainText("Piloto de caça durante a Primeira Guerra Mundial.")
    
    valid, msg = tab._validate_profile()
    
    assert valid, f"Perfil válido foi marcado como inválido: {msg}"
    assert msg == "", f"Mensagem de erro deveria estar vazia para perfil válido: {msg}"


def test_age_negative_when_ref_before_birth(qtbot: QtBot):
    """Testa que idade é negativa quando referência é antes do nascimento."""
    tab = ProfileTab()
    qtbot.addWidget(tab)
    
    # Nascimento em 1890
    tab.dob_edit.setDate(QDate(1890, 5, 15))
    
    # Referência antes do nascimento (1880)
    tab.update_reference_date(datetime(1880, 1, 1))
    
    # Idade deve ser N/A (representando inválido)
    assert tab.age_label.text() == 'N/A', f"Idade deveria ser N/A, obtido '{tab.age_label.text()}'"


def test_context_setting(qtbot: QtBot):
    """Testa definição de contexto campanha/piloto."""
    tab = ProfileTab()
    qtbot.addWidget(tab)
    
    # Define contexto
    tab.set_context("Campaign 1", "Hans Schmidt")
    
    # Verifica que contexto foi definido (via slug)
    expected_prefix = "campaigns/campaign_1/profiles/hans_schmidt"
    assert tab._prefix() == expected_prefix, f"Prefixo incorreto: {tab._prefix()}"


def test_save_button_disabled_initially(qtbot: QtBot):
    """Testa que botão salvar está desabilitado inicialmente."""
    tab = ProfileTab()
    qtbot.addWidget(tab)
    
    # Botão deve estar desabilitado inicialmente
    assert not tab.btn_save.isEnabled(), "Botão salvar deveria estar desabilitado inicialmente"


def test_compute_age_static_method():
    """Testa método estático de cálculo de idade."""
    dob = datetime(1890, 5, 15)
    ref = datetime(1918, 10, 1)
    
    age = ProfileTab._compute_age(dob, ref)
    
    assert age == 28, f"Idade calculada incorreta: {age}"
    
    # Testa aniversário ainda não ocorrido no ano
    ref_before_birthday = datetime(1918, 4, 1)
    age_before = ProfileTab._compute_age(dob, ref_before_birthday)
    
    assert age_before == 27, f"Idade antes do aniversário incorreta: {age_before}"
    
    # Testa referência antes do nascimento
    ref_invalid = datetime(1880, 1, 1)
    age_invalid = ProfileTab._compute_age(dob, ref_invalid)
    
    assert age_invalid == -1, f"Idade para referência inválida deveria ser -1: {age_invalid}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ── testes para set_rank / set_rank_with_insignia ────────────────────────

def test_set_rank_default_country_is_germany(qtbot):
    """Sem configuração prévia, o país padrão deve ser germany."""
    tab = ProfileTab()
    qtbot.addWidget(tab)

    assert tab._country_folder == "germany", (
        f"País padrão esperado 'germany', obtido '{tab._country_folder}'"
    )


def test_set_rank_with_insignia_stores_country_folder(qtbot):
    """set_rank_with_insignia deve persistir o country_folder na instância."""
    tab = ProfileTab()
    qtbot.addWidget(tab)

    tab.set_rank_with_insignia("Captain", country_folder="britain")

    assert tab._country_folder == "britain", (
        f"Esperado 'britain', obtido '{tab._country_folder}'"
    )


def test_set_rank_with_insignia_stores_country_folder_france(qtbot):
    """set_rank_with_insignia deve funcionar para qualquer nacionalidade."""
    tab = ProfileTab()
    qtbot.addWidget(tab)

    tab.set_rank_with_insignia("Adjudant", country_folder="france")

    assert tab._country_folder == "france", (
        f"Esperado 'france', obtido '{tab._country_folder}'"
    )


def test_set_rank_uses_stored_country_not_hardcoded_germany(qtbot):
    """set_rank deve usar o _country_folder armazenado, não 'germany' fixo.

    Este é o teste de regressão central do bug: após configurar o país para
    'britain', chamar set_rank() NÃO deve resetar o país para 'germany'.
    """
    tab = ProfileTab()
    qtbot.addWidget(tab)

    # Configura país britânico
    tab.set_rank_with_insignia("Lieutenant", country_folder="britain")
    assert tab._country_folder == "britain"

    # Chama set_rank — deve manter 'britain', não resetar para 'germany'
    tab.set_rank("Captain")

    assert tab._country_folder == "britain", (
        f"set_rank() resetou o país para '{tab._country_folder}' — "
        "esperado 'britain' (bug de hardcoding 'germany' ainda presente)"
    )


def test_set_rank_updates_rank_text_label(qtbot):
    """set_rank deve atualizar o label de texto da patente."""
    tab = ProfileTab()
    qtbot.addWidget(tab)

    tab.set_rank("Major")

    assert tab.rank_text_label.text() == "Major", (
        f"rank_text_label esperado 'Major', obtido '{tab.rank_text_label.text()}'"
    )


def test_set_rank_with_insignia_updates_rank_text_label(qtbot):
    """set_rank_with_insignia deve atualizar o label de texto da patente."""
    tab = ProfileTab()
    qtbot.addWidget(tab)

    tab.set_rank_with_insignia("Capitaine", country_folder="france")

    assert tab.rank_text_label.text() == "Capitaine", (
        f"rank_text_label esperado 'Capitaine', obtido '{tab.rank_text_label.text()}'"
    )


def test_set_rank_with_insignia_normalizes_country_folder(qtbot):
    """country_folder deve ser normalizado para lowercase."""
    tab = ProfileTab()
    qtbot.addWidget(tab)

    tab.set_rank_with_insignia("Captain", country_folder="BRITAIN")

    assert tab._country_folder == "britain", (
        f"Esperado 'britain' (lowercase), obtido '{tab._country_folder}'"
    )


def test_set_rank_country_persists_across_multiple_calls(qtbot):
    """O país configurado deve persistir por múltiplas chamadas a set_rank."""
    tab = ProfileTab()
    qtbot.addWidget(tab)

    tab.set_rank_with_insignia("Sergeant", country_folder="usa")

    tab.set_rank("Corporal")
    tab.set_rank("Private")
    tab.set_rank("General")

    assert tab._country_folder == "usa", (
        f"País esperado 'usa' após múltiplas chamadas, obtido '{tab._country_folder}'"
    )


def test_compute_ribbons_height_returns_min_when_empty(qtbot: QtBot):
    """_compute_ribbons_height retorna 56 quando não há ribbons."""
    tab = ProfileTab()
    qtbot.addWidget(tab)

    # Garantir que o layout está vazio
    tab._clear_ribbons()

    h = tab._compute_ribbons_height()
    assert h == 56, f"Estado vazio deve retornar 56px, obtido {h}px"


def test_compute_ribbons_height_respects_max(qtbot: QtBot):
    """_compute_ribbons_height não excede MAX_H=160px independente dos itens."""
    from PyQt5.QtWidgets import QToolButton
    from PyQt5.QtCore import QSize

    tab = ProfileTab()
    qtbot.addWidget(tab)
    tab.show()

    # Adicionar muitos botões para forçar múltiplas linhas
    tab._clear_ribbons()
    if tab._ribbons_layout:
        for i in range(20):
            btn = QToolButton()
            btn.setFixedSize(106, 106)
            tab._ribbons_layout.addWidget(btn)

    h = tab._compute_ribbons_height()
    assert h <= 160, f"Altura não deve exceder 160px, obtido {h}px"


def test_compute_ribbons_height_respects_min_when_filled(qtbot: QtBot):
    """_compute_ribbons_height retorna ao menos 80px quando há 1 ribbon."""
    from PyQt5.QtWidgets import QToolButton

    tab = ProfileTab()
    qtbot.addWidget(tab)
    tab.show()

    tab._clear_ribbons()
    if tab._ribbons_layout:
        btn = QToolButton()
        btn.setFixedSize(106, 106)
        tab._ribbons_layout.addWidget(btn)

    h = tab._compute_ribbons_height()
    assert h >= 80, f"Estado preenchido deve retornar ao menos 80px, obtido {h}px"


def test_set_ribbons_empty_sets_height_56(qtbot: QtBot):
    """set_ribbons com ids vazios aplica fixedHeight de 56px no scroll."""
    tab = ProfileTab()
    qtbot.addWidget(tab)
    tab.show()

    tab.set_ribbons("germany", earned_ids=set())

    if tab._ribbons_scroll:
        h = tab._ribbons_scroll.height()
        assert h == 56, (
            f"Estado vazio deve ter height=56px, obtido {h}px"
        )


def test_update_ribbons_height_method_exists(qtbot: QtBot):
    """ProfileTab deve expor _update_ribbons_height como método callable."""
    tab = ProfileTab()
    qtbot.addWidget(tab)

    assert hasattr(tab, "_update_ribbons_height"), (
        "ProfileTab deve ter método _update_ribbons_height"
    )
    assert callable(tab._update_ribbons_height), (
        "_update_ribbons_height deve ser callable"
    )


def test_compute_ribbons_height_method_exists(qtbot: QtBot):
    """ProfileTab deve expor _compute_ribbons_height como método callable."""
    tab = ProfileTab()
    qtbot.addWidget(tab)

    assert hasattr(tab, "_compute_ribbons_height"), (
        "ProfileTab deve ter método _compute_ribbons_height"
    )
    assert callable(tab._compute_ribbons_height), (
        "_compute_ribbons_height deve ser callable"
    )


def test_compute_ribbons_height_returns_int(qtbot: QtBot):
    """_compute_ribbons_height deve sempre retornar int."""
    tab = ProfileTab()
    qtbot.addWidget(tab)

    result = tab._compute_ribbons_height()
    assert isinstance(result, int), (
        f"_compute_ribbons_height deve retornar int, obtido {type(result)}"
    )
