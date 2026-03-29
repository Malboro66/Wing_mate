import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

pytest.importorskip("PyQt5")


def test_set_theme_updates_dscolors_class_identity():
    ds = importlib.import_module("app.ui.design_system")

    ds.set_theme("dark")
    assert ds.DSColors is ds.DarkColors

    ds.set_theme("light")
    assert ds.DSColors is ds.LightColors


def test_toast_level_styles_follow_active_theme():
    ds = importlib.import_module("app.ui.design_system")

    ds.set_theme("dark")
    dark_error = ds.DSFeedback.TOAST_LEVEL_STYLES["error"]
    dark_deep = ds.DSColors.DEEP

    ds.set_theme("light")
    light_error = ds.DSFeedback.TOAST_LEVEL_STYLES["error"]
    light_deep = ds.DSColors.DEEP

    assert dark_error != light_error
    assert dark_deep in dark_error
    assert light_deep in light_error


def test_get_toast_style_returns_theme_specific_css():
    ds = importlib.import_module("app.ui.design_system")

    ds.set_theme("dark")
    dark_css = ds.DSFeedback.get_toast_style("error")

    ds.set_theme("light")
    light_css = ds.DSFeedback.get_toast_style("error")

    assert dark_css
    assert light_css
    assert dark_css != light_css


def test_build_global_stylesheet_differs_between_themes_and_not_empty():
    ds = importlib.import_module("app.ui.design_system")

    ds.set_theme("dark")
    dark = ds.build_global_stylesheet()

    ds.set_theme("light")
    light = ds.build_global_stylesheet()

    assert dark
    assert light
    assert dark != light


def test_design_system_shim_reexports_work():
    from app.ui.design_system import DSColors, set_theme

    assert DSColors is not None
    assert callable(set_theme)
