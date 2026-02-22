from pathlib import Path


def test_main_app_uses_random_splash_folder_and_sound() -> None:
    src = Path("main_app.py").read_text(encoding="utf-8")
    assert '"app" / "assets" / "splash_optimized"' in src
    assert 'random.choice(images)' in src
    assert '"app" / "assets" / "sounds" / "airplane_engine_start.wav"' in src


def test_main_app_shows_splash_for_4_seconds() -> None:
    src = Path("main_app.py").read_text(encoding="utf-8")
    assert 'def _show_startup_splash(app: QApplication, duration_s: float = 4.0)' in src
    assert 'splash: Optional[QSplashScreen] = _show_startup_splash(app, duration_s=4.0)' in src
