import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_tracker_filters_victory_notifications_and_7day_threshold():
    src = Path("utils/war_propaganda_tracker.py").read_text(encoding="utf-8")
    assert "_VICTORY_TOKENS" in src
    assert "WINDOW_DAYS = 7" in src
    assert "THRESHOLD = 5" in src
    assert "register_event_from_notification" in src


def test_main_window_listens_notification_bus_and_opens_popup():
    src = Path("app/ui/main_window.py").read_text(encoding="utf-8")
    assert "WarPropagandaTracker" in src
    assert "register_event_from_notification(level, message)" in src
    assert "WarPropagandaPopup(" in src


def test_popup_has_1917_newspaper_style_and_photo_placeholder():
    src = Path("app/ui/war_propaganda_popup.py").read_text(encoding="utf-8")
    assert "GAZETA DA FRENTE" in src
    assert "Ano de 1917" in src
    assert "Foto do Piloto" in src
