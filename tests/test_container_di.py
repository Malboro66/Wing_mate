import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.container import AppContainer


def test_container_reuses_singletons_for_same_path(tmp_path: Path):
    container = AppContainer(str(tmp_path))

    parser_a = container.get_parser()
    parser_b = container.get_parser()
    assert parser_a is parser_b

    query_a = container.get_campaign_query_service()
    query_b = container.get_campaign_query_service()
    assert query_a is query_b


def test_container_resets_path_dependent_instances(tmp_path: Path):
    path_a = str(tmp_path / "a")
    path_b = str(tmp_path / "b")

    container = AppContainer(path_a)
    parser_a = container.get_parser()

    container.set_pwcgfc_path(path_b)
    parser_b = container.get_parser()

    assert parser_a is not parser_b


def test_container_exposes_squadron_app_service_singleton():
    container = AppContainer()

    svc_a = container.get_squadron_enrichment_application_service()
    svc_b = container.get_squadron_enrichment_application_service()

    assert svc_a is svc_b


def test_container_exposes_content_registry_singleton():
    container = AppContainer()

    reg_a = container.get_content_module_registry()
    reg_b = container.get_content_module_registry()

    assert reg_a is reg_b


def test_container_clears_parser_cache_before_reset(tmp_path: Path, monkeypatch):
    path_a = str(tmp_path / "a")
    path_b = str(tmp_path / "b")

    container = AppContainer(path_a)
    parser = container.get_parser()

    called = {"value": False}

    def fake_clear_cache():
        called["value"] = True

    monkeypatch.setattr(parser, "clear_cache", fake_clear_cache)

    container.set_pwcgfc_path(path_b)

    assert called["value"] is True
