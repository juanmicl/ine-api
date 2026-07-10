# ine/models/variables.py
"""Modelo del dominio VARIABLES."""

from __future__ import annotations

from ine.models._base import _BaseModel


class Variable(_BaseModel):
    """Una variable del INE (p. ej. "Total Nacional", código ``NAC``).

    Las variables son las dimensiones que estructuran las series (territorio,
    sexo, edad...). Cada variable tiene valores (categories) que se usan en los
    filtros ``tv`` / ``g``.
    """

    id: int | None = None
    nombre: str
    codigo: str | None = None
