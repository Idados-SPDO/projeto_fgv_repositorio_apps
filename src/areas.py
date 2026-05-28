"""Áreas fixas do domínio do Repositório de Aplicações."""
from __future__ import annotations

from typing import Optional


# (AREA_NAME, DISPLAY_NAME) — display em caixa alta
AREAS: list[tuple[str, str]] = [
    ("COWEB",             "COWEB"),
    ("COLETA",            "COLETA"),
    ("PRODUCAO_SETORIAL", "PRODUÇÃO SETORIAL"),
    ("GESTAO_DADOS",      "GESTÃO DE DADOS"),
    ("P&D",               "P&D"),
]

AREA_NAMES: list[str] = [a[0] for a in AREAS]
_DISPLAY: dict[str, str] = dict(AREAS)

# áreas ordenadas alfabeticamente pelo display name (usado nas abas)
AREAS_ALPHA: list[str] = sorted(AREA_NAMES, key=lambda a: _DISPLAY[a])


def display_name(area_name: Optional[str]) -> str:
    if area_name is None:
        return "(sem área)"
    return _DISPLAY.get(area_name, area_name)
