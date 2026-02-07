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
