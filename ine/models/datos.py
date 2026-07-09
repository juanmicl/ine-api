# ine/models/datos.py
from __future__ import annotations

from datetime import datetime

from ine.models._base import ConFecha, _BaseModel


class DatosObservacion(ConFecha):
    fecha: datetime
    valor: float
    anyo: int
    fk_periodo: int
    secreto: bool = False


class DatosSerie(_BaseModel):
    cod: str
    nombre: str
    data: list[DatosObservacion] = []
