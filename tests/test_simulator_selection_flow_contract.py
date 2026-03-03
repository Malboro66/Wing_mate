import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_root_window_uses_qstackedwidget_and_settings_gear_navigation():
    src = Path("app/ui/simulator_selection_main_window.py").read_text(encoding="utf-8")
    assert "QStackedWidget" in src
    assert "self.btn_settings" in src
    assert "SP_FileDialogDetailedView" in src
    assert "QSizePolicy.Expanding" in src
    assert "settings_global_button" in src
    assert "self._go_to(self._idx_settings)" in src


def test_era_widget_buttons_start_disabled_and_are_gated():
    src = Path("app/ui/era_selection_widget.py").read_text(encoding="utf-8")
    assert "self.btn_ww1.setEnabled(False)" in src
    assert "self.btn_ww2.setEnabled(False)" in src
    assert "attempted_when_disabled" in src
    assert "setMinimumWidth(420)" in src


def test_ww1_widget_routes_only_pwcg_to_wing_mate_and_others_to_future():
    src = Path("app/ui/ww1_simulator_selection_widget.py").read_text(encoding="utf-8")
    assert "self.btn_il2_fc.clicked.connect(self.open_future_feature.emit)" in src
    assert "self.btn_rof.clicked.connect(self.open_future_feature.emit)" in src
    assert "self.btn_rof_pwcg.clicked.connect(self.open_future_feature.emit)" in src
    assert "self.btn_il2_fc_pwcg.clicked.connect(self.open_wing_mate.emit)" in src


def test_settings_widget_validates_paths_and_notifies_status():
    src = Path("app/ui/settings_widget.py").read_text(encoding="utf-8")
    assert "QFileDialog.getExistingDirectory" in src
    assert "status.setText(self._t(\"path_valid\"))" in src
    assert "status.setText(self._t(\"path_invalid\"))" in src
    assert "notify_warning(self._t(\"path_invalid_toast\"))" in src
    assert "self.settings_changed.emit()" in src


def test_settings_widget_retranslate_updates_labels_and_buttons():
    src = Path("app/ui/settings_widget.py").read_text(encoding="utf-8")
    assert "for key, (lbl, _edit, browse, _status, label_key) in self._fields.items():" in src
    assert "browse.setText(self._t(\"browse\"))" in src
