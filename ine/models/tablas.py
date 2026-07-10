# ine/models/tablas.py
"""Modelos del dominio TABLAS.

:class:`Tabla` anida :class:`~ine.models.maestros.Periodicidad` y convierte
``ultima_modificacion`` de epoch-ms a :class:`~datetime.datetime`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import field_validator

from ine.models._base import _BaseModel
from ine.models.maestros import Periodicidad


class Tabla(_BaseModel):
    """Una tabla (vista predefinida) del INE.

    ``ultima_modificacion`` llega como *epoch* en ms y se convierte a
    :class:`~datetime.datetime` (tz UTC). ``periodicidad`` es una lista de
    objetos :class:`Periodicidad` anidados.
    """

    id: int | None = None
    nombre: str
    codigo: str | None = None
    fk_periodicidad: int | None = None
    periodicidad: list[Periodicidad] = []
    fk_publicacion: int | None = None
    fk_periodo_ini: int | None = None
    anyo_periodo_ini: str | None = None
    fecha_ref_fin: str | None = None
    ultima_modificacion: datetime | None = None

    @field_validator("ultima_modificacion", mode="before")
    @classmethod
    def _epoch_ms(cls, v: object) -> object:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return datetime.fromtimestamp(v / 1000, tz=UTC)
        return v


class Grupo(_BaseModel):
    """Un grupo de variables dentro de una tabla (filtro predefinido)."""

    id: int | None = None
    nombre: str
