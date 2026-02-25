# ===================================================================
# Wing Mate - main_app.py (entrada da aplicação)
# ===================================================================

import sys
import logging
import logging.handlers
import tempfile
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt, QLockFile
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtGui import QIcon, QPixmap

from app.ui.main_window import MainWindow
from utils.observability import publish_release_report, record_startup_time
from utils.structured_logger import StructuredLogger


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
structured_logger = StructuredLogger("IL2CampaignAnalyzer")


def _pick_splash_image() -> Optional[Path]:
    splash_dir = Path(__file__).resolve().parent / "app" / "assets" / "splash_optimized"
    if not splash_dir.exists():
        return None

    images = [
        p for p in splash_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
    ]
    if not images:
        return None
    return random.choice(images)


def _play_startup_sound() -> None:
    sound_file = Path(__file__).resolve().parent / "app" / "assets" / "sounds" / "airplane_engine_start.wav"
    if not sound_file.exists():
        logger.warning("Som de abertura não encontrado: %s", sound_file)
        return

    try:
        qt_multimedia = __import__("PyQt5.QtMultimedia", fromlist=["QSound"])
        qsound = getattr(qt_multimedia, "QSound", None)
        if qsound is not None:
            qsound.play(str(sound_file))
            return
    except Exception as e:
        logger.debug("QtMultimedia não disponível para áudio de splash: %s", e)

    logger.warning("Não foi possível reproduzir áudio de splash (QtMultimedia indisponível).")


def _show_startup_splash(app: QApplication, duration_s: float = 4.0) -> Optional[QSplashScreen]:
    splash_image = _pick_splash_image()
    if splash_image is None:
        logger.warning("Nenhuma imagem de splash encontrada em app/assets/splash_optimized")
        _play_startup_sound()
        return None

    pixmap = QPixmap(str(splash_image))
    if pixmap.isNull():
        logger.warning("Falha ao carregar splash: %s", splash_image)
        _play_startup_sound()
        return None

    splash = QSplashScreen(pixmap)
    splash.setWindowFlag(Qt.WindowStaysOnTopHint, True)
    splash.show()
    app.processEvents()

    logger.info("Splash de abertura: %s", splash_image.name)
    _play_startup_sound()

    end_time = time.monotonic() + max(0.0, duration_s)
    while time.monotonic() < end_time:
        app.processEvents()
        time.sleep(0.01)

    return splash


if __name__ == '__main__':
    app_start_t0 = time.perf_counter()
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

    splash: Optional[QSplashScreen] = _show_startup_splash(app, duration_s=4.0)

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
        if splash is not None:
            splash.finish(win)
        win.show()
        record_startup_time(structured_logger, (time.perf_counter() - app_start_t0) * 1000.0)
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
        try:
            reports_dir = Path(__file__).resolve().parent / "logs" / "observability"
            release_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
            baseline = reports_dir / "baseline.json"
            report_path = publish_release_report(
                structured_logger,
                release_tag=release_tag,
                output_dir=reports_dir,
                baseline_path=baseline if baseline.exists() else None,
            )
            baseline.parent.mkdir(parents=True, exist_ok=True)
            baseline.write_text(report_path.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception as e:
            logger.debug("Falha ao publicar relatório de observabilidade: %s", e)

        if lock and lock.isLocked():
            lock.unlock()
        sys.exit(exit_code)