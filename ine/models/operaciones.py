# ine/models/operaciones.py
"""Modelo del dominio OPERACIONES (Fase 5).

:class:`~ine.models.operaciones.Operacion` es la ficha de una operación
estadística del INE (IPC, EPA, etc.). Sus campos ``id``/``codigo``/``cod_ioe``
son los identificadores que aceptan los endpoints (``Id``, ``Codigo``,
``IOEXXXX``).
"""

from __future__ import annotations

from ine.models._base import _BaseModel


class Operacion(_BaseModel):
    """Una operación estadística del INE (registro OperacionesJSON).

    Identificadores: ``id`` (Tempus3 ``Id``), ``codigo`` (``Codigo``) y
    ``cod_ioe`` (``IOEXXXX`` del INE); cualquiera sirve para identificar la
    operación en los métodos del cliente.
    """

    id: int | None = None
    cod_ioe: str | None = None
    nombre: str
    codigo: str | None = None
    url: str | None = None
