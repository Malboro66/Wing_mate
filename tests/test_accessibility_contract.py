import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_main_window_has_focus_order_and_accessible_names():
    src = Path("app/ui/main_window.py").read_text(encoding="utf-8")
    assert 'self.campaign_combo.setAccessibleName("campaign_selector")' in src
    assert 'self.btn_copy_path.setAccessibleName("copiar_caminho_button")' in src
    assert 'self.tabs.setAccessibleName("main_tabs")' in src
    assert 'self.setTabOrder(self.campaign_combo, self.btn_copy_path)' in src
    assert 'self.setTabOrder(self.btn_copy_path, self.tabs)' in src


def test_medals_tab_has_accessibility_labels_and_focus_proxy():
    src = Path("app/ui/medals_tab.py").read_text(encoding="utf-8")
    assert 'self._search_edit.setAccessibleName("medals_search_input")' in src
    assert 'self._icon_list.setAccessibleName("medals_icon_list")' in src
    assert 'self._table.setAccessibleName("medals_table")' in src
    assert "self.setFocusProxy(self._search_edit)" in src


def test_feedback_and_state_tokens_are_consistent_in_critical_screens():
    main = Path("app/ui/main_window.py").read_text(encoding="utf-8")
    missions = Path("app/ui/missions_tab.py").read_text(encoding="utf-8")
    squadron = Path("app/ui/squadron_tab.py").read_text(encoding="utf-8")
    profile = Path("app/ui/profile_tab.py").read_text(encoding="utf-8")

    assert "SkeletonWidget" in main
    assert "ToastWidget" in main
    assert "NotificationBus" in profile
    assert "show_actionable_error" in profile

    for token in ("DSStyles.STATE_INFO", "DSStyles.STATE_SUCCESS", "DSStyles.STATE_WARNING", "DSStyles.STATE_ERROR"):
        assert token in missions
        assert token in squadron
