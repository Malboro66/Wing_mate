from pathlib import Path


def test_tabs_expose_set_language_and_retranslate_hooks() -> None:
    missions_src = Path("app/ui/missions_tab.py").read_text(encoding="utf-8")
    squadron_src = Path("app/ui/squadron_tab.py").read_text(encoding="utf-8")
    profile_src = Path("app/ui/profile_tab.py").read_text(encoding="utf-8")

    assert "def set_language(self, language_code: str) -> None:" in missions_src
    assert "def retranslate(self) -> None:" in missions_src

    assert "def set_language(self, language_code: str) -> None:" in squadron_src
    assert "def retranslate(self) -> None:" in squadron_src

    assert "def set_language(self, language_code: str) -> None:" in profile_src
    assert "def retranslate(self) -> None:" in profile_src


def test_main_window_propagates_language_to_child_tabs() -> None:
    src = Path("app/ui/main_window.py").read_text(encoding="utf-8")
    assert "for tab_widget in (self.missions_tab, self.squadron_tab, self.profile_tab):" in src
    assert "tab_widget.set_language(self._language_code)" in src
