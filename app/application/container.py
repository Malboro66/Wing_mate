# -*- coding: utf-8 -*-
"""
Wing Mate — app/application/container.py  (versão ampliada)

Adiciona suporte ao cp.db como fonte de dados alternativa ao PWCG JSON.
A detecção é automática: se um arquivo cp.db existir no caminho informado
(ou em sub-pastas conhecidas), o repositório SQLite é preferido.
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
    "data/cp.db",
    "career/cp.db",
    "il2/cp.db",
    "Flying Circus/cp.db",
)


def _find_cp_db(base: Path) -> Optional[Path]:
    """Busca cp.db em locais candidatos a partir de base."""
    for rel in _CP_DB_CANDIDATES:
        candidate = base / rel
        if candidate.exists() and candidate.is_file():
            return candidate
    # Busca recursiva limitada a 3 níveis
    for depth in range(1, 4):
        pattern = "/".join(["*"] * depth) + "/cp.db"
        found = list(base.glob(pattern))
        if found:
            return found[0]
    return None


class AppContainer:
    """Container de DI manual com suporte a fonte JSON (PWCG) e SQLite (cp.db)."""

    def __init__(self, pwcgfc_path: Optional[str] = None) -> None:
        self._pwcgfc_path = pwcgfc_path or ""
        self._cp_db_path: Optional[Path] = None

        # JSON source
        self._parser: Optional[IL2DataParser] = None
        self._processor: Optional[IL2DataProcessor] = None
        self._campaign_repo: Optional[JsonCampaignRepository] = None
        self._campaign_query: Optional[CampaignQueryService] = None
        self._squadron_app: Optional[SquadronEnrichmentApplicationService] = None
        self._content_registry: Optional[ContentModuleRegistry] = None

        # SQLite source (lazy)
        self._cp_db_repo = None  # CpDbCampaignRepository — importado on demand

    # ------------------------------------------------------------------ #
    # Configuração de caminho                                              #
    # ------------------------------------------------------------------ #

    def set_pwcgfc_path(self, path: str) -> None:
        normalized = path or ""
        if normalized == self._pwcgfc_path:
            return
        if self._parser is not None:
            self._parser.clear_cache()
        self._pwcgfc_path = normalized
        self._reset_json_sources()
        self._reset_cp_db()

        # Tenta localizar cp.db automaticamente no novo caminho
        if normalized:
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
        """Retorna True se um cp.db válido foi encontrado/configurado."""
        return self._cp_db_path is not None and self._cp_db_path.exists()

    # ------------------------------------------------------------------ #
    # Reset helpers                                                        #
    # ------------------------------------------------------------------ #

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
        Retorna CpDbCampaignRepository (importado on-demand para não forçar
        dependência de sqlite3 quando cp.db não está presente).
        """
        if self._cp_db_repo is None:
            if not self.has_cp_db():
                raise RuntimeError("cp.db não configurado ou não encontrado.")
            from app.infrastructure.cp_db_repository import CpDbCampaignRepository
            self._cp_db_repo = CpDbCampaignRepository(self._cp_db_path)
        return self._cp_db_repo

    def list_campaigns(self) -> list[str]:
        """
        Lista campanhas disponíveis.
        - Se cp.db disponível: retorna IDs de carreiras.
        - Caso contrário: usa parser JSON.
        """
        if self.has_cp_db():
            try:
                return self.get_cp_db_repository().list_career_ids()
            except Exception:
                logger.exception("Falha ao listar carreiras do cp.db; fallback JSON")
        return self.get_parser().get_campaigns()

    def process_campaign(self, campaign_name: str) -> dict:
        """
        Ponto único de processamento de campanha.
        - cp.db disponível → usa CpDbCampaignRepository.process_career()
        - caso contrário  → usa IL2DataProcessor.process_campaign()
        """
        if self.has_cp_db():
            try:
                return self.get_cp_db_repository().process_career(campaign_name)
            except Exception:
                logger.exception(
                    "cp.db falhou ao processar '%s'; tentando fallback JSON", campaign_name
                )
        return self.get_processor().process_campaign(campaign_name)

    # ------------------------------------------------------------------ #
    # Serviços independentes de fonte                                      #
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
