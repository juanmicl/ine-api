# ine/models/maestros.py
"""Modelos del dominio MAESTROS (diccionarios del INE).

Esquemas verificados empíricamente con sondas a la API Tempus. La mayoría de
estos endpoints **no están documentados en el OpenAPI del INE**.

Heredan :class:`~ine.models._base._BaseModel` (auto-normaliza claves
PascalCase→snake; ``extra='ignore'``). :class:`Clasificacion` usa
:class:`~ine.models._base.ConFecha` para convertir ``fecha`` de epoch-ms a
:class:`~datetime.datetime`.
"""

from __future__ import annotations

from datetime import datetime

from ine.models._base import ConFecha, _BaseModel


class Escala(_BaseModel):
    """Escala numérica del INE (p. ej. unidades, decenas, miles).

    Recurso ``ESCALAS`` (lista) y ``ESCALA/{id}`` (individual). **No documentado
    en OpenAPI.**
    """

    id: int | None = None
    nombre: str
    factor: str | None = None
    codigo: str | None = None
    abrev: str | None = None


class Unidad(_BaseModel):
    """Unidad de medida del INE (p. ej. personas, euros, toneladas).

    Recurso ``UNIDADES`` (lista), ``UNIDAD/{id}`` (individual) y
    ``UNIDADES_OPERACION/{op}`` (por operación). **No documentado en OpenAPI.**
    """

    id: int | None = None
    nombre: str
    codigo: str | None = None
    abrev: str | None = None


class Periodicidad(_BaseModel):
    """Periodicidad temporal del INE (p. ej. mensual, trimestral, anual).

    Recurso ``PERIODICIDADES`` (lista) y ``PERIODICIDAD/{id}`` (individual).
    """

    id: int | None = None
    nombre: str
    codigo: str | None = None


class Periodo(_BaseModel):
    """Periodo concreto dentro de una periodicidad (p. ej. "Enero 2024").

    Recurso ``PERIODO/{id}`` (individual). **No documentado en OpenAPI.**
    Esquema más rico que el resto de maestros.
    """

    id: int | None = None
    valor: int | None = None
    fk_periodicidad: int | None = None
    dia_inicio: str | None = None
    mes_inicio: str | None = None
    codigo: str | None = None
    nombre: str | None = None
    nombre_largo: str | None = None


class Clasificacion(ConFecha):
    """Clasificación estadística del INE (p. ej. CNAE, CCN).

    Recurso ``CLASIFICACIONES`` (lista) y ``CLASIFICACIONES_OPERACION/{op}``
    (por operación). ``fecha`` llega como *epoch* en ms y se convierte a
    :class:`~datetime.datetime` vía :class:`~ine.models._base.ConFecha`.
    """

    id: int | None = None
    nombre: str
    fecha: datetime | None = None
