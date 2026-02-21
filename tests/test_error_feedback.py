import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ui.error_feedback import build_actionable_error_text


def test_build_actionable_error_text_includes_file_and_hint():
    text = build_actionable_error_text(
        title="Erro",
        summary="Falha ao processar",
        action_hint="Tente novamente",
        file_path="/tmp/a.json",
    )

    assert "Falha ao processar" in text
    assert "Arquivo: /tmp/a.json" in text
    assert "Ação sugerida: Tente novamente" in text
