import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_no_non_critical_information_dialogs_left():
    offenders = []
    for path in Path("app/ui").glob("*.py"):
        src = path.read_text(encoding="utf-8")
        if "QMessageBox.information(" in src:
            offenders.append(str(path))

    assert not offenders, f"QMessageBox.information encontrado em: {offenders}"


def test_notification_bus_exposes_instance_and_send_api():
    src = Path("utils/notification_bus.py").read_text(encoding="utf-8")
    assert "def instance(" in src
    assert "def send(" in src
