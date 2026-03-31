from pathlib import Path


def test_aces_roundel_layout_is_centered_and_column_is_wide_enough():
    src = Path("app/ui/aces_tab.py").read_text(encoding="utf-8")
    assert "ROUNDEL_COLUMN_WIDTH = 120" in src
    assert "ROUNDEL_SIZE = 36" in src
    assert "cell_layout = QHBoxLayout(cell_widget)" in src
    assert "cell_layout.addWidget(label, 0, Qt.AlignCenter)" in src
