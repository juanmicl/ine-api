# ine/models/series.py
"""Modelos del dominio SERIES (Fase 5).

Cubren ``SERIE`` (catálogo de series) y ``VALORES_SERIE`` (valores de
variables de una serie). El INE usa ``COD`` (mayúsculas, no ``Codigo``) como
identificador textual de una serie; el ``model_validator(mode='before')`` de
:class:`ine.models._base._BaseModel` lo normaliza a ``cod``.

Los campos anidados ``Periodicidad`` / ``Escala`` / ``Unidad`` / ``Clasificacion``
y los prefijados ``T3_*`` que envía el INE se descartan vía ``extra='ignore'``
(los modelos viven en el dominio MAESTROS, fuera del alcance prioritario).
"""

from __future__ import annotations

from ine.models._base import _BaseModel
from ine.models.operaciones import Operacion


class Serie(_BaseModel):
    """Una serie temporal del INE (registro SeriesJSON).

    ``cod`` es el identificador textual (``COD`` en el payload); ``id`` el
    numérico. ``operacion`` es el ``OperacionesJSON`` anidado cuando el cliente
    pide ``det=2`` (o equivalente).
    """

    id: int | None = None
    cod: str | None = None
    nombre: str
    decimales: int
    fk_operacion: int | None = None
    operacion: Operacion | None = None
    fk_periodicidad: int | None = None
    fk_publicacion: int | None = None
    fk_clasificacion: int | None = None
    fk_escala: int | None = None
    fk_unidad: int | None = None


class Valor(_BaseModel):
    """Un valor de variable asociado a una serie (registro ValoresSerieJSON)."""

    id: int | None = None
    nombre: str
    codigo: str | None = None
    fk_variable: int | None = None
    t3_variable: str | None = None
