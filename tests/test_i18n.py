import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ui.i18n import AppI18n


def test_i18n_supports_portuguese_and_english_labels():
    assert AppI18n.LANG_LABELS[AppI18n.PT_BR] == "Português"
    assert AppI18n.LANG_LABELS[AppI18n.EN_US] == "English"


def test_i18n_translates_main_window_keys():
    assert AppI18n.t("campaign_label", AppI18n.PT_BR) == "Campanha:"
    assert AppI18n.t("campaign_label", AppI18n.EN_US) == "Campaign:"
    assert AppI18n.t("sync_data", AppI18n.EN_US) == "Sync Data"
