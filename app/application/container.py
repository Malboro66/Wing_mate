from __future__ import annotations

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


class AppContainer:
    """Container simples de DI manual para bootstrap de dependências."""

    def __init__(self, pwcgfc_path: Optional[str] = None) -> None:
        self._pwcgfc_path = pwcgfc_path or ""
        self._parser: Optional[IL2DataParser] = None
        self._processor: Optional[IL2DataProcessor] = None
        self._campaign_repo: Optional[JsonCampaignRepository] = None
        self._campaign_query: Optional[CampaignQueryService] = None
        self._squadron_app: Optional[SquadronEnrichmentApplicationService] = None
        self._content_registry: Optional[ContentModuleRegistry] = None

    def set_pwcgfc_path(self, path: str) -> None:
        normalized = path or ""
        if normalized == self._pwcgfc_path:
            return
        if self._parser is not None:
            self._parser.clear_cache()
        self._pwcgfc_path = normalized
        self._parser = None
        self._processor = None
        self._campaign_repo = None
        self._campaign_query = None
        self._content_registry = None

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

    def get_squadron_enrichment_application_service(self) -> SquadronEnrichmentApplicationService:
        if self._squadron_app is None:
            self._squadron_app = SquadronEnrichmentApplicationService(
                SquadronEnrichmentService()
            )
        return self._squadron_app

    def get_content_module_registry(self) -> ContentModuleRegistry:
        if self._content_registry is None:
            assets_root = (Path(__file__).resolve().parents[1] / "assets")
            self._content_registry = ContentModuleRegistry(assets_root)
            self._content_registry.load_external_modules()
        return self._content_registry
