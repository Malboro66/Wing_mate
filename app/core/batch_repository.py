from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from app.core.data_parser import IL2DataParser


@dataclass(frozen=True)
class BatchReadStats:
    requested: int
    loaded: int


class JsonBatchRepository:
    """Camada de repositório com APIs bulk-first para leitura e resolução."""

    def __init__(self, parser: IL2DataParser) -> None:
        self._parser = parser

    def load_many(self, paths: Iterable[Path]) -> Tuple[Dict[Path, Optional[Any]], BatchReadStats]:
        path_list: List[Path] = list(paths)
        payload = self._parser.get_json_many(path_list)
        loaded = sum(1 for value in payload.values() if value is not None)
        return payload, BatchReadStats(requested=len(path_list), loaded=loaded)

    def resolve_many(
        self,
        loaded_payloads: Dict[Path, Optional[Any]],
        resolver: Callable[[Path, Any], Optional[Any]],
    ) -> List[Any]:
        resolved: List[Any] = []
        for path, payload in loaded_payloads.items():
            if payload is None:
                continue
            item = resolver(path, payload)
            if item is not None:
                resolved.append(item)
        return resolved
