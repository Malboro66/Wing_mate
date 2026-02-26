import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_main_window_keeps_queued_connection_for_data_loaded_signal():
    source = Path("app/ui/main_window.py").read_text(encoding="utf-8")
    assert "data_loaded.connect(self._on_data_loaded, Qt.QueuedConnection)" in source


def test_main_window_uses_skeleton_and_keeps_tabs_enabled_while_busy():
    source = Path("app/ui/main_window.py").read_text(encoding="utf-8")
    assert "self.tabs.setEnabled(True)" in source
    assert "self._set_sync_skeletons_visible(self._busy" in source


def test_main_window_uses_notification_bus_with_queued_connection():
    source = Path("app/ui/main_window.py").read_text(encoding="utf-8")
    assert "notification_bus.notified.connect(self._on_notification, Qt.QueuedConnection)" in source


def test_non_critical_sync_feedback_uses_toast_not_messagebox():
    source = Path("app/ui/main_window.py").read_text(encoding="utf-8")
    assert 'notify_warning(self._t("select_folder_warning"))' in source
    assert "QMessageBox.warning" not in source


def test_main_window_handles_parser_without_cache_metrics_gracefully():
    source = Path("app/ui/main_window.py").read_text(encoding="utf-8")
    assert 'getattr(parser, "get_cache_metrics", lambda: {"hits": 0, "misses": 0})()' in source


def test_main_window_exposes_language_selector_with_supported_options():
    source = Path("app/ui/main_window.py").read_text(encoding="utf-8")
    assert "self.language_combo = QComboBox()" in source
    assert "AppI18n.LANG_LABELS[AppI18n.PT_BR]" in source
    assert "AppI18n.LANG_LABELS[AppI18n.EN_US]" in source
    assert "ui/language" in source
