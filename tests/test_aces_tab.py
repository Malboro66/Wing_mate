# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - tests/test_aces_tab.py
# Testes para normalização de países e mapeamento de roundels
# ===================================================================

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import types

# Stub mínimo para importar AcesTab sem dependência real de PyQt5 no ambiente de teste
if "PyQt5" not in sys.modules:
    qt_mod = types.ModuleType("PyQt5")
    qtcore = types.ModuleType("PyQt5.QtCore")
    qtgui = types.ModuleType("PyQt5.QtGui")
    qtwidgets = types.ModuleType("PyQt5.QtWidgets")

    class _Dummy:
        def __init__(self, *args, **kwargs):
            pass

    class _QtDummy:
        AlignCenter = 0
        KeepAspectRatio = 0
        SmoothTransformation = 0

    qtcore.Qt = _QtDummy
    qtcore.pyqtSignal = lambda *args, **kwargs: _Dummy()
    qtgui.QPixmap = _Dummy
    qtwidgets.QWidget = _Dummy
    qtwidgets.QVBoxLayout = _Dummy
    qtwidgets.QHBoxLayout = _Dummy
    qtwidgets.QTableWidget = _Dummy
    qtwidgets.QTableWidgetItem = _Dummy
    qtwidgets.QHeaderView = _Dummy
    qtwidgets.QLabel = _Dummy
    qtwidgets.QAbstractItemView = _Dummy

    sys.modules["PyQt5"] = qt_mod
    sys.modules["PyQt5.QtCore"] = qtcore
    sys.modules["PyQt5.QtGui"] = qtgui
    sys.modules["PyQt5.QtWidgets"] = qtwidgets

from app.ui.aces_tab import AcesTab


class TestNormalizeCountryCode:
    """Testa o método de normalização de variações de nomes de países."""

    def test_germany_canonical_passthrough(self):
        assert AcesTab._normalize_country_code("GERMANY") == "GERMANY"

    def test_german_variant_maps_to_germany(self):
        assert AcesTab._normalize_country_code("GERMAN") == "GERMANY"

    def test_deutsch_variant_maps_to_germany(self):
        assert AcesTab._normalize_country_code("DEUTSCH") == "GERMANY"

    def test_prussian_variant_maps_to_germany(self):
        assert AcesTab._normalize_country_code("PRUSSIAN") == "GERMANY"

    def test_britain_canonical_passthrough(self):
        assert AcesTab._normalize_country_code("BRITAIN") == "BRITAIN"

    def test_great_britain_maps_to_britain(self):
        assert AcesTab._normalize_country_code("GREAT BRITAIN") == "BRITAIN"

    def test_rfc_maps_to_britain(self):
        assert AcesTab._normalize_country_code("RFC") == "BRITAIN"

    def test_rfc_with_qualifier_maps_to_britain(self):
        """Variação composta como 'RFC (BRITISH)' deve ser normalizada."""
        assert AcesTab._normalize_country_code("RFC (BRITISH)") == "BRITAIN"

    def test_uk_maps_to_britain(self):
        assert AcesTab._normalize_country_code("UK") == "BRITAIN"

    def test_england_maps_to_britain(self):
        assert AcesTab._normalize_country_code("ENGLAND") == "BRITAIN"

    def test_british_maps_to_britain(self):
        assert AcesTab._normalize_country_code("BRITISH") == "BRITAIN"

    def test_france_canonical_passthrough(self):
        assert AcesTab._normalize_country_code("FRANCE") == "FRANCE"

    def test_french_maps_to_france(self):
        assert AcesTab._normalize_country_code("FRENCH") == "FRANCE"

    def test_usa_canonical_passthrough(self):
        assert AcesTab._normalize_country_code("USA") == "USA"

    def test_american_maps_to_usa(self):
        assert AcesTab._normalize_country_code("AMERICAN") == "USA"

    def test_united_states_maps_to_usa(self):
        assert AcesTab._normalize_country_code("UNITED STATES") == "USA"

    def test_belgium_canonical_passthrough(self):
        assert AcesTab._normalize_country_code("BELGIUM") == "BELGIUM"

    def test_belgian_maps_to_belgium(self):
        assert AcesTab._normalize_country_code("BELGIAN") == "BELGIUM"

    def test_belgian_army_maps_to_belgium(self):
        """Variação composta como 'BELGIAN ARMY' deve ser normalizada."""
        assert AcesTab._normalize_country_code("BELGIAN ARMY") == "BELGIUM"

    def test_unknown_country_returns_original(self):
        """Países sem mapeamento devem ser retornados sem alteração."""
        assert AcesTab._normalize_country_code("RUSSIA") == "RUSSIA"
        assert AcesTab._normalize_country_code("ITALY") == "ITALY"
        assert AcesTab._normalize_country_code("AUSTRIA") == "AUSTRIA"

    def test_empty_string_returns_empty(self):
        assert AcesTab._normalize_country_code("") == ""


class TestCountryRoundelsDict:
    """Testa o dicionário COUNTRY_ROUNDELS após expansão."""

    def test_all_canonical_keys_present(self):
        """Todas as chaves canônicas esperadas devem estar no dict."""
        required = {"GERMANY", "BRITAIN", "FRANCE", "USA", "BELGIUM", "BELGIAN"}
        missing = required - set(AcesTab.COUNTRY_ROUNDELS.keys())
        assert not missing, f"Chaves canônicas ausentes em COUNTRY_ROUNDELS: {missing}"

    def test_all_values_are_png_filenames(self):
        """Todos os valores devem ser nomes de arquivo .png."""
        for key, value in AcesTab.COUNTRY_ROUNDELS.items():
            assert value.endswith(".png"), (
                f"Valor para '{key}' não é .png: '{value}'"
            )

    def test_no_alias_keys_in_dict(self):
        """O dict não deve conter aliases — só chaves canônicas.
        Aliases são resolvidos por _normalize_country_code.
        """
        aliases_that_should_not_be_keys = {
            "GREAT BRITAIN", "UK", "RFC", "ENGLAND", "BRITISH",
            "GERMAN", "DEUTSCH", "PRUSSIAN",
            "FRENCH",
            "AMERICAN", "US", "UNITED STATES",
            "BELGE",
        }
        found = aliases_that_should_not_be_keys & set(AcesTab.COUNTRY_ROUNDELS.keys())
        assert not found, (
            f"Aliases encontrados como chaves diretas no dict (devem ser tratados "
            f"pelo _normalize_country_code): {found}"
        )

    def test_britain_and_germany_map_to_existing_theme_files(self):
        """As roundels mais críticas devem apontar para os arquivos corretos."""
        assert AcesTab.COUNTRY_ROUNDELS["BRITAIN"] == "theme_rfc.png"
        assert AcesTab.COUNTRY_ROUNDELS["GERMANY"] == "theme_german.png"
        assert AcesTab.COUNTRY_ROUNDELS["FRANCE"] == "theme_french.png"
        assert AcesTab.COUNTRY_ROUNDELS["USA"] == "theme_american.png"
        assert AcesTab.COUNTRY_ROUNDELS["BELGIUM"] == "theme_belgium.png"


class TestNormalizeAndLookupIntegration:
    """Testa o pipeline completo: variação bruta → normalização → lookup."""

    def _lookup(self, raw_country: str) -> str | None:
        """Simula o pipeline de _create_roundel_widget sem instanciar widgets Qt."""
        canonical = AcesTab._normalize_country_code(raw_country.upper())
        return AcesTab.COUNTRY_ROUNDELS.get(canonical)

    def test_great_britain_resolves_to_rfc_png(self):
        assert self._lookup("Great Britain") == "theme_rfc.png"

    def test_rfc_resolves_to_rfc_png(self):
        assert self._lookup("RFC") == "theme_rfc.png"

    def test_uk_resolves_to_rfc_png(self):
        assert self._lookup("UK") == "theme_rfc.png"

    def test_german_resolves_to_german_png(self):
        assert self._lookup("German") == "theme_german.png"

    def test_french_resolves_to_french_png(self):
        assert self._lookup("French") == "theme_french.png"

    def test_american_resolves_to_american_png(self):
        assert self._lookup("American") == "theme_american.png"

    def test_belgian_army_resolves_to_belgium_png(self):
        assert self._lookup("Belgian Army") == "theme_belgium.png"

    def test_russia_resolves_to_none(self):
        """Países sem asset devem retornar None (fallback de texto aceitável)."""
        assert self._lookup("Russia") is None

    def test_italy_resolves_to_none(self):
        assert self._lookup("Italy") is None

    def test_empty_resolves_to_none(self):
        assert self._lookup("") is None
