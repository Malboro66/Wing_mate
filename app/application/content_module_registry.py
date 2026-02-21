from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ContentModule:
    """Módulo de conteúdo (plugin) com metadados e diretório base."""

    module_id: str
    name: str
    category: str
    base_path: Path
    version: str = "1.0.0"
    enabled: bool = True


class ContentModuleRegistry:
    """Registro simples de módulos de conteúdo para reduzir acoplamento a paths fixos."""

    def __init__(self, assets_root: Path) -> None:
        self._assets_root = assets_root
        self._modules: Dict[str, ContentModule] = {}
        self._register_builtin_modules()

    def _register_builtin_modules(self) -> None:
        builtins = [
            ContentModule("medals", "Medalhas", "medals", self._assets_root / "medals"),
            ContentModule("squadrons", "Esquadrões", "squadrons", self._assets_root / "squadrons"),
            ContentModule("ranks", "Patentes", "ranks", self._assets_root / "ranks"),
        ]
        for module in builtins:
            self._modules[module.module_id] = module

    def load_external_modules(self, modules_root: Optional[Path] = None) -> int:
        """Carrega manifests externos (`module.json`) de plugins de conteúdo."""
        root = modules_root or (self._assets_root / "modules")
        if not root.exists() or not root.is_dir():
            return 0

        loaded = 0
        for manifest in sorted(root.glob("*/module.json")):
            try:
                raw = json.loads(manifest.read_text(encoding="utf-8"))
                module = self._parse_manifest(raw, manifest.parent)
                self._modules[module.module_id] = module
                loaded += 1
            except (OSError, ValueError, json.JSONDecodeError):
                continue
        return loaded

    def _parse_manifest(self, raw: Dict[str, object], base_dir: Path) -> ContentModule:
        module_id = str(raw.get("id", "")).strip()
        name = str(raw.get("name", "")).strip()
        category = str(raw.get("category", "")).strip()
        version = str(raw.get("version", "1.0.0")).strip() or "1.0.0"
        enabled = bool(raw.get("enabled", True))
        rel_path = str(raw.get("path", "")).strip()

        if not module_id or not name or not category or not rel_path:
            raise ValueError("Manifest inválido: id/name/category/path são obrigatórios")

        return ContentModule(
            module_id=module_id,
            name=name,
            category=category,
            base_path=(base_dir / rel_path).resolve(),
            version=version,
            enabled=enabled,
        )

    def get_module(self, module_id: str) -> Optional[ContentModule]:
        return self._modules.get(module_id)

    def list_modules(self, only_enabled: bool = True) -> List[ContentModule]:
        items = list(self._modules.values())
        if only_enabled:
            items = [m for m in items if m.enabled]
        return sorted(items, key=lambda m: m.module_id)

    def resolve(self, module_id: str, *parts: str) -> Path:
        module = self.get_module(module_id)
        if not module:
            raise KeyError(f"Módulo não encontrado: {module_id}")
        return module.base_path.joinpath(*parts)
