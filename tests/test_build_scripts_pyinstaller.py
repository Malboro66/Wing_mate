from build_scripts.build_with_pyinstaller import _asset_separator


def test_asset_separator_is_platform_compatible(monkeypatch):
    monkeypatch.setattr("build_scripts.build_with_pyinstaller.sys.platform", "win32")
    assert _asset_separator() == ";"

    monkeypatch.setattr("build_scripts.build_with_pyinstaller.sys.platform", "linux")
    assert _asset_separator() == ":"
