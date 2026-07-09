# ine/models/datos.py
"""Modelos del dominio DATOS (Fase 5).

:class:`~ine.models.datos.DatosSerie` agrupa las observaciones de una serie;
cada :class:`~ine.models.datos.DatosObservacion` es un dato puntual
(fecha + valor).
"""

from __future__ import annotations

from datetime import datetime

from ine.models._base import ConFecha, _BaseModel


class DatosObservacion(ConFecha):
    """Una observación puntual de una serie (registro DatosJSON).

    ``fecha`` llega del INE como *epoch* en milisegundos y se normaliza a
    :class:`~datetime.datetime` (tz UTC) vía
    :class:`~ine.models._base.ConFecha`. ``secreto`` marca los datos ocultos
    por secreto estadístico.
    """

    fecha: datetime
    valor: float
    anyo: int
    fk_periodo: int
    secreto: bool = False


class DatosSerie(_BaseModel):
    """Las observaciones de una serie (registro DatosSerieJSON).

    ``cod`` es el identificador textual de la serie; ``data``, la lista de
    observaciones (:class:`DatosObservacion`).
    """

    cod: str
    nombre: str
    data: list[DatosObservacion] = []
