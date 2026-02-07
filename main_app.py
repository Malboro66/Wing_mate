# ===================================================================
# Wing Mate - main_app.py (entrada da aplicação)
# ===================================================================

import sys
import logging
import logging.handlers
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt, QLockFile
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QMessageBox

from app.ui.main_window import MainWindow


def _setup_logging(level: int = logging.INFO) -> logging.Logger:
    logger_name = "IL2CampaignAnalyzer"
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(level)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    try:
        base_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
        logs_dir = base_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_filename = logs_dir / f"wingmate_{datetime.now():%Y%m%d}.log"

        fh = logging.handlers.RotatingFileHandler(
            filename=str(log_filename),
            maxBytes=5 * 1024 * 1024,
            backupCount=7,
            encoding='utf-8'
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except (PermissionError, OSError) as e:
        logger.warning(f"Não foi possível inicializar arquivo de log: {e}")
    except Exception as e:
        logger.warning(f"Erro inesperado ao configurar logging: {e}")

    logger.propagate = False
    return logger


logger: logging.Logger = _setup_logging(logging.INFO)


if __name__ == '__main__':
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # Atributos não disponíveis nesta versão do Qt
        pass
    except Exception as e:
        logger.debug(f"Erro ao configurar atributos da aplicação: {e}")

    app: QApplication = QApplication(sys.argv)
    app.setApplicationName("Wing Mate")
    app.setOrganizationName("WingMate")

    # Ícone global da aplicação (alguns ambientes exibem ícone do app no dock/taskbar)
    try:
        app_icon_path: Path = Path(__file__).resolve().parent / "app" / "assets" / "icons" / "app_icon.png"
        pm: QPixmap = QPixmap(str(app_icon_path))
        if not pm.isNull():
            app.setWindowIcon(QIcon(pm))
        else:
            logger.warning(f"Ícone global não carregado: {app_icon_path}")
    except (FileNotFoundError, PermissionError) as e:
        logger.debug(f"Falha ao acessar arquivo de ícone: {e}")
    except Exception as e:
        logger.debug(f"Falha ao definir ícone global: {e}")

    # Evitar múltiplas instâncias
    lock: Optional[QLockFile] = None
    try:
        lockfile_path: str = str(Path(tempfile.gettempdir()) / "wingmate.lock")
        lock = QLockFile(lockfile_path)
        lock.setStaleLockTime(0)
        if not lock.tryLock(100):
            QMessageBox.warning(None, "Instância em execução", "Outra instância já está em execução.")
            sys.exit(0)
    except (PermissionError, OSError) as e:
        logger.debug(f"Não foi possível criar arquivo de lock: {e}")
        lock = None
    except Exception as e:
        logger.debug(f"Erro inesperado ao configurar lock: {e}")
        lock = None

    try:
        win: MainWindow = MainWindow()
        win.show()
        exit_code: int = app.exec_()
    except ImportError as e:
        logger.exception(f"Falha ao importar módulos da interface: {e}")
        QMessageBox.critical(None, "Erro", "Falha ao carregar componentes da interface gráfica.")
        exit_code = 1
    except RuntimeError as e:
        logger.exception(f"Falha ao inicializar a interface: {e}")
        QMessageBox.critical(None, "Erro", "Falha ao iniciar a interface gráfica.")
        exit_code = 1
    except Exception as e:
        logger.exception(f"Falha inesperada ao iniciar a interface: {e}")
        QMessageBox.critical(None, "Erro", "Falha ao iniciar a interface gráfica.")
        exit_code = 1
    finally:
        if lock and lock.isLocked():
            lock.unlock()
        sys.exit(exit_code)