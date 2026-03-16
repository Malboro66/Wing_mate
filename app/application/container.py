# -*- coding: utf-8 -*-
"""
Wing Mate â€” app/application/container.py  (versÃ£o ampliada)

Adiciona suporte ao cp.db como fonte de dados alternativa ao PWCG JSON.
A detecÃ§Ã£o Ã© automÃ¡tica: se um arquivo cp.db existir no caminho informado
(ou em sub-pastas conhecidas), o repositÃ³rio SQLite Ã© preferido.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.application.campaign_query_service import CampaignQueryService
from app.application.content_module_registry import ContentModuleRegistry
from app.application.squadron_enrichment_application_service import (
    SquadronEnrichmentApplicationService,
)
from app.core.data_parser import IL2DataParser
from app.core.data_processor import IL2DataProcessor
from app.core.repositories import JsonCampaignRepository
from app.core.squadron_enrichment_service import SquadronEnrichmentService

logger = logging.getLogger("IL2CampaignAnalyzer")


# Caminhos relativos onde o jogo costuma colocar o cp.db
_CP_DB_CANDIDATES = (
    "cp.db",
    "Career/cp.db",
    "career/cp.db",
    "data/Career/cp.db",
    "data/career/cp.db",
    "data/cp.db",
    "il2/cp.db",
    "Flying Circus/cp.db",
)


def _find_cp_db(base: Path) -> Optional[Path]:
    """Busca cp.db em locais candidatos a partir de base.

    Suporta tanto caminho raiz do jogo quanto pasta data/Career, com variações
    de capitalização do nome do arquivo em sistemas case-sensitive.
    """
    for rel in _CP_DB_CANDIDATES:
        candidate = base / rel
        if candidate.exists() and candidate.is_file():
            return candidate

    # Busca recursiva limitada a 3 níveis (case-insensitive por variantes).
    # Inclui também o diretório base para cobrir nomes como ./CP.DB.
    for name_variant in ("cp.db", "Cp.db", "CP.db", "CP.DB"):
        direct_candidate = base / name_variant
        if direct_candidate.exists() and direct_candidate.is_file():
            return direct_candidate

        for depth in range(1, 4):
            pattern = "/".join(["*"] * depth) + f"/{name_variant}"
            found = list(base.glob(pattern))
            if found:
                return found[0]
    return None


class AppContainer:
    """Container de DI manual com suporte a fonte JSON (PWCG) e SQLite (cp.db)."""

    SOURCE_AUTO = "auto"
    SOURCE_PWCG_JSON = "pwcg_json"
    SOURCE_IL2_VANILLA = "il2_vanilla"
    _VALID_SOURCE_MODES = {SOURCE_AUTO, SOURCE_PWCG_JSON, SOURCE_IL2_VANILLA}

    def __init__(self, pwcgfc_path: Optional[str] = None) -> None:
        self._pwcgfc_path = pwcgfc_path or ""
        self._cp_db_path: Optional[Path] = None
        self._source_mode = self.SOURCE_AUTO

        # JSON source
        self._parser: Optional[IL2DataParser] = None
        self._processor: Optional[IL2DataProcessor] = None
        self._campaign_repo: Optional[JsonCampaignRepository] = None
        self._campaign_query: Optional[CampaignQueryService] = None
        self._squadron_app: Optional[SquadronEnrichmentApplicationService] = None
        self._content_registry: Optional[ContentModuleRegistry] = None

        # SQLite source (lazy)
        self._cp_db_repo = None  # CpDbCampaignRepository â€” importado on demand

    # ------------------------------------------------------------------ #
    # ConfiguraÃ§Ã£o de caminho                                              #
    # ------------------------------------------------------------------ #

    def set_source_mode(self, mode: str) -> None:
        normalized = str(mode or self.SOURCE_AUTO).strip().lower()
        if normalized not in self._VALID_SOURCE_MODES:
            normalized = self.SOURCE_AUTO

        if normalized == self._source_mode:
            return

        self._source_mode = normalized
        self._reset_json_sources()

        if self._source_mode == self.SOURCE_PWCG_JSON:
            self._reset_cp_db()
            self._cp_db_path = None

    def get_source_mode(self) -> str:
        return self._source_mode

    def set_pwcgfc_path(self, path: str) -> None:
        normalized = path or ""
        if normalized == self._pwcgfc_path:
            return

        if self._parser is not None:
            self._parser.clear_cache()

        self._pwcgfc_path = normalized
        self.reset()
        self._cp_db_path = None

        # Tenta localizar cp.db automaticamente no novo caminho
        # (exceto quando o modo foi fixado para PWCG JSON).
        if normalized and self._source_mode != self.SOURCE_PWCG_JSON:
            found = _find_cp_db(Path(normalized))
            if found:
                self.set_cp_db_path(found)
                logger.info("cp.db detectado automaticamente: %s", found)

    def set_cp_db_path(self, db_path: Path) -> None:
        """Define (ou troca) o caminho do cp.db explicitamente."""
        self._cp_db_path = db_path
        self._reset_cp_db()
        logger.info("Fonte cp.db configurada: %s", db_path)

    def has_cp_db(self) -> bool:
        """Retorna True se um cp.db vÃ¡lido foi encontrado/configurado."""
        return self._cp_db_path is not None and self._cp_db_path.exists() and self._cp_db_path.is_file()

    def _should_use_cp_db(self) -> bool:
        if self._source_mode == self.SOURCE_PWCG_JSON:
            return False
        return self.has_cp_db()

    # ------------------------------------------------------------------ #
    # Reset helpers                                                        #
    # ------------------------------------------------------------------ #

    def reset(self) -> None:
        """Invalida instâncias lazily carregadas dependentes de caminho/fonte."""
        self._reset_json_sources()
        self._reset_cp_db()

    def _reset_json_sources(self) -> None:
        self._parser = None
        self._processor = None
        self._campaign_repo = None
        self._campaign_query = None
        self._content_registry = None

    def _reset_cp_db(self) -> None:
        if self._cp_db_repo is not None:
            try:
                self._cp_db_repo.close()
            except Exception:
                pass
        self._cp_db_repo = None

    # ------------------------------------------------------------------ #
    # Fonte JSON (PWCG)                                                    #
    # ------------------------------------------------------------------ #

    def get_parser(self) -> IL2DataParser:
        if self._parser is None:
            self._parser = IL2DataParser(self._pwcgfc_path)
        return self._parser

    def get_processor(self) -> IL2DataProcessor:
        if self._processor is None:
            self._processor = IL2DataProcessor(self._pwcgfc_path)
        return self._processor

    def create_processor(self, pwcgfc_path: str) -> IL2DataProcessor:
        return IL2DataProcessor(pwcgfc_path)

    def get_campaign_repository(self) -> JsonCampaignRepository:
        if self._campaign_repo is None:
            self._campaign_repo = JsonCampaignRepository(self.get_parser())
        return self._campaign_repo

    def get_campaign_query_service(self) -> CampaignQueryService:
        if self._campaign_query is None:
            self._campaign_query = CampaignQueryService(self.get_campaign_repository())
        return self._campaign_query

    # ------------------------------------------------------------------ #
    # Fonte SQLite (cp.db)                                                 #
    # ------------------------------------------------------------------ #

    def get_cp_db_repository(self):
        """
        Retorna CpDbCampaignRepository (importado on-demand para nÃ£o forÃ§ar
        dependÃªncia de sqlite3 quando cp.db nÃ£o estÃ¡ presente).
        """
        if self._cp_db_repo is None:
            if not self.has_cp_db():
                raise RuntimeError("cp.db nÃ£o configurado ou nÃ£o encontrado.")
            from app.infrastructure.cp_db_repository import CpDbCampaignRepository
            self._cp_db_repo = CpDbCampaignRepository(self._cp_db_path)
        return self._cp_db_repo

    def list_campaigns(self) -> list[str]:
        """
        Lista campanhas disponÃ­veis.
        - Se cp.db disponÃ­vel: retorna IDs de carreiras.
        - Caso contrÃ¡rio: usa parser JSON.
        """
        if self._should_use_cp_db():
            try:
                return self.get_cp_db_repository().list_career_ids()
            except Exception:
                logger.exception("Falha ao listar carreiras do cp.db; fallback JSON")
        return self.get_parser().get_campaigns()

    def process_campaign(self, campaign_name: str) -> dict:
        """
        Ponto Ãºnico de processamento de campanha.
        - cp.db disponÃ­vel â†’ usa CpDbCampaignRepository.process_career()
        - caso contrÃ¡rio  â†’ usa IL2DataProcessor.process_campaign()
        """
        if self._should_use_cp_db():
            try:
                return self.get_cp_db_repository().process_career(campaign_name)
            except Exception:
                logger.exception(
                    "cp.db falhou ao processar '%s'; tentando fallback JSON", campaign_name
                )
        return self.get_processor().process_campaign(campaign_name)

    # ------------------------------------------------------------------ #
    # ServiÃ§os independentes de fonte                                      #
    # ------------------------------------------------------------------ #

    def get_squadron_enrichment_application_service(self) -> SquadronEnrichmentApplicationService:
        if self._squadron_app is None:
            self._squadron_app = SquadronEnrichmentApplicationService(
                SquadronEnrichmentService()
            )
        return self._squadron_app

    def get_content_module_registry(self) -> ContentModuleRegistry:
        if self._content_registry is None:
            assets_root = Path(__file__).resolve().parents[1] / "assets"
            self._content_registry = ContentModuleRegistry(assets_root)
            self._content_registry.load_external_modules()
        return self._content_registry
