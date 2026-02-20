from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List



@dataclass
class ViewState:
    state: str
    message: str


class MissionsViewModel:
    def state_for_loaded_missions(self, missions: List[Dict[str, Any]]) -> ViewState:
        if not missions:
            return ViewState("empty", "Nenhuma missão disponível para os filtros atuais.")
        return ViewState("success", f"{len(missions)} missões carregadas.")

    def filter_visibility(self, missions: List[Dict[str, Any]], row_values: List[List[str]], query: str) -> List[bool]:
        q = (query or "").strip().lower()
        if not q:
            return [True] * len(row_values)

        visible: List[bool] = []
        for idx, cols in enumerate(row_values):
            desc = ""
            if 0 <= idx < len(missions):
                desc = str(missions[idx].get("description", "")).lower()
            haystack = " | ".join([c.lower() for c in cols] + [desc])
            visible.append(q in haystack)
        return visible

    def state_for_visible_count(self, count: int) -> ViewState:
        if count == 0:
            return ViewState("empty", "Nenhuma missão corresponde ao filtro informado.")
        return ViewState("success", f"{count} missões visíveis.")


class SquadronViewModel:
    def state_for_members(self, members: List[Dict[str, Any]]) -> ViewState:
        if not members:
            return ViewState("empty", "Nenhum membro de esquadrão disponível.")
        return ViewState("success", "Dados do esquadrão carregados.")

    def filter_visibility(self, rows: List[Dict[str, str]], query: str) -> List[bool]:
        q = (query or "").strip().lower()
        if not q:
            return [True] * len(rows)

        visible: List[bool] = []
        for row in rows:
            haystack = " | ".join(
                [
                    str(row.get("name", "")).lower(),
                    str(row.get("rank", "")).lower(),
                    str(row.get("victories", "")).lower(),
                    str(row.get("missions", "")).lower(),
                    str(row.get("status", "")).lower(),
                ]
            )
            visible.append(q in haystack)
        return visible

    def state_for_visible_count(self, count: int) -> ViewState:
        if count == 0:
            return ViewState("empty", "Nenhum piloto corresponde ao filtro informado.")
        return ViewState("success", f"{count} pilotos visíveis.")
