from __future__ import annotations

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from app.ui.simulator_selection_main_window import MainWindow


def run() -> int:
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Wing Mate")

    win = MainWindow()
    win.resize(1280, 820)
    win.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(run())
