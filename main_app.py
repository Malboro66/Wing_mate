# ===================================================================
# Wing Mate - main_app.py (entrada da aplicação)
# ===================================================================

from __future__ import annotations

import logging
import logging.handlers
import random
import sys
import tempfile
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from PyQt5.QtCore import QLockFile, Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QDesktopWidget, QMessageBox, QSplashScreen

from app.ui.design_system import load_custom_fonts, build_global_stylesheet

from utils.observability import (
    publish_release_report,
    record_startup_error,
    record_startup_phase,
    record_startup_time,
)

import cache_manager
from utils.structured_logger import StructuredLogger

STARTUP_TIMEOUT_S = 10.0


def _setup_logging(level: int = logging.INFO) -> logging.Logger:
    logger_name = "IL2CampaignAnalyzer"
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(level)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    try:
        base_dir = Path(__file__).parent if "__file__" in globals() else Path.cwd()
        logs_dir = base_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_filename = logs_dir / f"wingmate_{datetime.now():%Y%m%d}.log"

        fh = logging.handlers.RotatingFileHandler(
            filename=str(log_filename),
            maxBytes=5 * 1024 * 1024,
            backupCount=7,
            encoding="utf-8",
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except (PermissionError, OSError) as e:
        logger.warning("Não foi possível inicializar arquivo de log: %s", e)
    except Exception as e:
        logger.warning("Erro inesperado ao configurar logging: %s", e)

    logger.propagate = False
    return logger


logger: logging.Logger = _setup_logging(logging.INFO)
structured_logger = StructuredLogger("IL2CampaignAnalyzer")


class StartupProfiler:
    def __init__(self) -> None:
        self._phase_t0 = time.perf_counter()
        self._completed_phases: list[str] = []

    def mark(self, label: str) -> None:
        elapsed_ms = (time.perf_counter() - self._phase_t0) * 1000.0
        logger.info("[startup] %s: %.1f ms", label, elapsed_ms)
        record_startup_phase(label, elapsed_ms)
        self._completed_phases.append(label)
        self._phase_t0 = time.perf_counter()

    @property
    def completed_phases(self) -> list[str]:
        return list(self._completed_phases)


def _load_startup_cache() -> dict[str, Any]:
    cached_value = cache_manager.get("startup:splash:last:v1")
    if isinstance(cached_value, dict):
        logger.info("[startup] cache hit: startup_cache carregado")
        return cached_value

    logger.info("[startup] cache miss: startup_cache ausente")
    return {}


def _save_startup_cache(cache_data: dict[str, Any]) -> None:
    cache_manager.set("startup:splash:last:v1", cache_data, expire=7 * 24 * 3600)


def _pick_splash_image() -> Optional[Path]:
    splash_dir = Path(__file__).resolve().parent / "app" / "assets" / "splash_optimized"
    if not splash_dir.exists():
        return None

    cache = _load_startup_cache()
    cached_splash = cache.get("last_splash")
    if isinstance(cached_splash, str):
        cached_path = Path(cached_splash)
        if cached_path.exists() and cached_path.parent == splash_dir:
            return cached_path

    images = [
        p
        for p in splash_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
    ]
    if not images:
        return None

    picked = random.choice(images)
    _save_startup_cache({"last_splash": str(picked)})
    return picked


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

    # Não bloquear startup na thread principal: o fechamento é controlado após a janela principal.
    splash.setProperty("minimum_display_s", max(0.0, float(duration_s)))
    splash.setProperty("shown_monotonic", time.monotonic())
    return splash



def _watchdog_start(timeout_s: float, phase_provider: Callable[[], list[str]]) -> threading.Timer:
    def _on_timeout() -> None:
        logger.critical("[startup] timeout atingido após %.1fs; fases concluídas: %s", timeout_s, phase_provider())

    timer = threading.Timer(timeout_s, _on_timeout)
    timer.daemon = True
    timer.start()
    return timer


def _center_window_on_screen(win: Any) -> None:
    frame_geometry = win.frameGeometry()
    screen_center = QDesktopWidget().availableGeometry(win).center()
    frame_geometry.moveCenter(screen_center)
    win.move(frame_geometry.topLeft())



def _wait_for_splash_minimum_duration(app: QApplication, splash: Optional[QSplashScreen]) -> None:
    if splash is None:
        return

    shown_monotonic = float(splash.property("shown_monotonic") or time.monotonic())
    min_display_s = float(splash.property("minimum_display_s") or 0.0)
    end_time = shown_monotonic + min_display_s

    while time.monotonic() < end_time:
        app.processEvents()
        time.sleep(0.01)


if __name__ == "__main__":
    cache_manager.inicializar_sessao()
    app_start_t0 = time.perf_counter()
    profiler = StartupProfiler()
    startup_watchdog = _watchdog_start(STARTUP_TIMEOUT_S, lambda: profiler.completed_phases)
    exit_code = 1
    lock: Optional[QLockFile] = None

    try:
        try:
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        except AttributeError:
            pass
        profiler.mark("qt atributos configurados")

        app: QApplication = QApplication(sys.argv)
        app.setApplicationName("Wing Mate")
        load_custom_fonts()
        app.setStyleSheet(build_global_stylesheet())
        app.setOrganizationName("WingMate")
        profiler.mark("qapplication inicializada")

        try:
            app_icon_path: Path = Path(__file__).resolve().parent / "app" / "assets" / "icons" / "app_icon.png"
            pm: QPixmap = QPixmap(str(app_icon_path))
            if not pm.isNull():
                app.setWindowIcon(QIcon(pm))
            else:
                logger.warning("Ícone global não carregado: %s", app_icon_path)
        except (FileNotFoundError, PermissionError) as e:
            logger.debug("Falha ao acessar arquivo de ícone: %s", e)
        profiler.mark("ícone carregado")

        splash: Optional[QSplashScreen] = _show_startup_splash(app, duration_s=4.0)
        profiler.mark("splash exibido")

        try:
            lockfile_path: str = str(Path(tempfile.gettempdir()) / "wingmate.lock")
            lock = QLockFile(lockfile_path)
            lock.setStaleLockTime(0)
            if not lock.tryLock(100):
                QMessageBox.warning(None, "Instância em execução", "Outra instância já está em execução.")
                exit_code = 0
                raise SystemExit
        except (PermissionError, OSError) as e:
            logger.debug("Não foi possível criar arquivo de lock: %s", e)
            lock = None
        profiler.mark("controle de instância concluído")

        try:
            # import lazy para reduzir custo na fase de imports do módulo main_app
            from app.ui.simulator_selection_main_window import MainWindow

            win = MainWindow()
            _center_window_on_screen(win)
            _wait_for_splash_minimum_duration(app, splash)
            if splash is not None:
                splash.finish(win)
            win.show()
        except Exception as exc:
            logger.exception("Falha ao construir/mostrar MainWindow")
            raise RuntimeError(str(exc)) from exc
        profiler.mark("janela principal interativa")

        startup_total_ms = (time.perf_counter() - app_start_t0) * 1000.0
        record_startup_time(structured_logger, startup_total_ms)
        logger.info("[startup] total: %.1f ms", startup_total_ms)

        exit_code = app.exec_()

    except SystemExit:
        pass
    except Exception as e:
        startup_error = f"{type(e).__name__}: {e}"
        record_startup_error(startup_error)
        logger.error("[startup] erro: %s", startup_error)
        logger.debug("[startup] traceback completo:\n%s", traceback.format_exc())
        try:
            QMessageBox.critical(None, "Erro", "Falha ao iniciar a interface gráfica.")
        except Exception:
            logger.debug("Falha ao exibir QMessageBox de erro de startup")
        exit_code = 1
    finally:
        startup_watchdog.cancel()
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
