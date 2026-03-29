from __future__ import annotations

from wingmate.core.container.service_container import ServiceContainer
from wingmate.core.events.event_bus import EventBus
from wingmate.infrastructure.cache.memory_cache import MemoryCache
from wingmate.infrastructure.repositories.json_campaign_repository import JsonCampaignRepository


class AppFactory:
    """Bootstrap layer that wires base services while keeping legacy UI runtime."""

    def __init__(self) -> None:
        self.container = ServiceContainer()

    def build_container(self) -> ServiceContainer:
        self.container.register(EventBus, EventBus())
        self.container.register(MemoryCache, MemoryCache())
        self.container.register(JsonCampaignRepository, JsonCampaignRepository())
        return self.container

    def start(self) -> int:
        self.build_container()
        from main_app import run

        return run()
