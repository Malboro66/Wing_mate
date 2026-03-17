# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - tests/test_passive_tabs_contract.py
# Garante que abas PyQt5 não acessam dados via self.parent() ou
# self.window() — padrão que retorna QTabWidget, não MainWindow.
# ===================================================================

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


_FORBIDDEN_DATA_ATTRS = frozenset({
    "current_data",
    "pwcgfc_path",
    "campaign_combo",
    "sync_thread",
    "_busy",
    "settings",
    "container",
    "_validated_missions",
    "selected_mission_index",
})


def _collect_parent_data_accesses(source: str, filepath: Path) -> list[str]:
    """
    Detecta via AST chamadas do tipo:
        self.parent().<attr>
        self.window().<attr>
        self.parent().parent().<attr>
    onde <attr> pertence ao conjunto de atributos de dados proibidos.

    Não reporta usos legítimos como:
        super().__init__(parent)
        QDialog(parent=self)
        SkeletonWidget(parent=tab)
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    offenders = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue

        if node.attr not in _FORBIDDEN_DATA_ATTRS:
            continue

        value = node.value
        if not isinstance(value, ast.Call):
            continue

        func = value.func
        if not (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "self"
            and func.attr in ("parent", "window")
        ):
            continue

        offenders.append(
            f"{filepath.relative_to(Path.cwd())}:{node.col_offset} "
            f"— self.{func.attr}().{node.attr}"
        )

    return offenders


def test_no_tab_accesses_data_via_parent_or_window():
    """
    Nenhuma aba em app/ui/ deve acessar dados da MainWindow via
    self.parent() ou self.window(). Abas devem receber dados
    exclusivamente por setters explícitos chamados pela MainWindow.
    """
    ui_dir = Path("app/ui")
    if not ui_dir.exists():
        ui_dir = Path(__file__).resolve().parents[1] / "app" / "ui"

    all_offenders = []

    for py_file in sorted(ui_dir.glob("*.py")):
        source = py_file.read_text(encoding="utf-8")
        offenders = _collect_parent_data_accesses(source, py_file)
        all_offenders.extend(offenders)

    assert not all_offenders, (
        "Abas acessando dados da MainWindow via self.parent() ou self.window():\n"
        + "\n".join(f"  {o}" for o in all_offenders)
        + "\n\nCorreção: criar setter explícito na aba e chamar via MainWindow._on_data_loaded()."
    )


def test_tabs_have_explicit_data_setters_not_pull_methods():
    """
    Contrato positivo: abas com dados devem expor setters explícitos.
    Verifica que os setters-padrão existem nos arquivos das abas.
    """
    expected_setters = {
        "missions_tab.py": "def set_missions(",
        "aces_tab.py": "def set_aces(",
        "squadron_tab.py": "def set_squadron(",
        "medals_tab.py": "def set_context(",
    }

    ui_dir = Path("app/ui")
    if not ui_dir.exists():
        ui_dir = Path(__file__).resolve().parents[1] / "app" / "ui"

    missing = []
    for filename, expected_sig in expected_setters.items():
        filepath = ui_dir / filename
        if not filepath.exists():
            missing.append(f"{filename}: arquivo não encontrado")
            continue
        source = filepath.read_text(encoding="utf-8")
        if expected_sig not in source:
            missing.append(f"{filename}: setter '{expected_sig}' ausente")

    assert not missing, (
        "Abas sem setter explícito de dados:\n"
        + "\n".join(f"  {m}" for m in missing)
    )


def test_main_window_pushes_data_to_all_tabs():
    """
    Contrato de integração: verifica que MainWindow._on_data_loaded
    chama os setters de todas as abas principais — padrão push.
    """
    main_window_src = Path("app/ui/main_window.py").read_text(encoding="utf-8")

    required_pushes = [
        "missions_tab.set_missions(",
        "aces_tab.set_aces(",
        "squadron_tab.set_squadron(",
        "medals_tab.set_context(",
    ]

    missing = [call for call in required_pushes if call not in main_window_src]

    assert not missing, (
        "MainWindow não empurra dados para todas as abas via _on_data_loaded:\n"
        + "\n".join(f"  {m}" for m in missing)
        + "\n\nAdicionar as chamadas ausentes em MainWindow._on_data_loaded()."
    )
