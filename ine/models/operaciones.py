# ine/models/operaciones.py
from __future__ import annotations

from ine.models._base import _BaseModel


class Operacion(_BaseModel):
    id: int | None = None
    cod_ioe: str | None = None
    nombre: str
    codigo: str | None = None
    url: str | None = None
