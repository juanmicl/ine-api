# ine/models/publicaciones.py
"""Modelos del dominio PUBLICACIONES.

:class:`Publicacion` anida :class:`~ine.models.maestros.Periodicidad` (el INE
envía ``Periodicidad: [{...}]`` dentro de cada publicación). Los campos
``T3_*``/``Operacion`` anidados se descartan vía ``extra='ignore'``.

:class:`PublicacionFecha` usa :class:`~ine.models._base.ConFecha` para convertir
``fecha`` de epoch-ms a :class:`~datetime.datetime`.
"""

from __future__ import annotations

from datetime import datetime

from ine.models._base import ConFecha, _BaseModel
from ine.models.maestros import Periodicidad


class Publicacion(_BaseModel):
    """Una publicación estadística del INE (p. ej. "Coyuntura Turística").

    ``periodicidad`` es una lista de objetos :class:`Periodicidad` anidados que
    el INE envía dentro de cada publicación.
    """

    id: int | None = None
    nombre: str
    url: str | None = None
    fk_periodicidad: int | None = None
    periodicidad: list[Periodicidad] = []
    fk_pub_fecha_act: int | None = None


class PublicacionFecha(ConFecha):
    """Una fecha/volumen de una publicación (p. ej. "Enero 2011").

    ``fecha`` llega como *epoch* en ms y se convierte a
    :class:`~datetime.datetime` vía :class:`~ine.models._base.ConFecha`.
    """

    id: int | None = None
    nombre: str | None = None
    fecha: datetime | None = None
    anyo: int | None = None
    fk_publicacion: int | None = None
    fk_periodo: int | None = None
