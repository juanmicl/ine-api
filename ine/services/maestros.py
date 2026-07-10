# ine/services/maestros.py
"""Servicio de maestros (diccionarios del INE): escalas, unidades, periodos,
periodicidades y clasificaciones.

Primer dominio que usa :meth:`Backend.get_one` para los endpoints de recurso
individual (escala/unidad/periodo/periodicidad). 7 de los 10 endpoints **no
están documentados en el OpenAPI del INE** (descubiertos empíricamente).
"""

from __future__ import annotations

from typing import Any

from ine._urls import (
    clasificaciones_operacion_path,
    clasificaciones_path,
    escala_path,
    escalas_path,
    periodicidad_path,
    periodicidades_path,
    periodo_path,
    unidad_path,
    unidades_operacion_path,
    unidades_path,
)
from ine.models.maestros import (
    Clasificacion,
    Escala,
    Periodicidad,
    Periodo,
    Unidad,
)
from ine.services._base import AsyncBaseService, BaseService


class MaestrosService(BaseService):
    """Diccionarios del INE (escalas, unidades, periodos, periodicidades,
    clasificaciones).
    """

    # --- Escalas ---

    # NO DOCUMENTADO en OpenAPI
    def escalas(self, *, raw: bool = False) -> list[Escala] | list[dict[str, Any]]:
        """Lista todas las escalas numéricas.

        Recurso ``ESCALAS``.
        """
        data = self._backend.get_list(escalas_path(self._lang))
        if raw:
            return data
        return [Escala.model_validate(d) for d in data]

    # NO DOCUMENTADO en OpenAPI
    def escala(self, id: int, *, raw: bool = False) -> Escala | dict[str, Any]:
        """Devuelve una escala por id.

        Recurso ``ESCALA/{id}``.
        """
        data = self._backend.get_one(escala_path(self._lang, id))
        if raw:
            return data
        return Escala.model_validate(data)

    # --- Unidades ---

    # NO DOCUMENTADO en OpenAPI
    def unidades(self, *, raw: bool = False) -> list[Unidad] | list[dict[str, Any]]:
        """Lista todas las unidades de medida.

        Recurso ``UNIDADES``.
        """
        data = self._backend.get_list(unidades_path(self._lang))
        if raw:
            return data
        return [Unidad.model_validate(d) for d in data]

    # NO DOCUMENTADO en OpenAPI
    def unidad(self, id: int, *, raw: bool = False) -> Unidad | dict[str, Any]:
        """Devuelve una unidad por id.

        Recurso ``UNIDAD/{id}``.
        """
        data = self._backend.get_one(unidad_path(self._lang, id))
        if raw:
            return data
        return Unidad.model_validate(data)

    # NO DOCUMENTADO en OpenAPI
    def unidades_operacion(
        self, op: str, *, raw: bool = False
    ) -> list[Unidad] | list[dict[str, Any]]:
        """Lista las unidades de una operación.

        Recurso ``UNIDADES_OPERACION/{op}``.
        """
        data = self._backend.get_list(unidades_operacion_path(self._lang, op))
        if raw:
            return data
        return [Unidad.model_validate(d) for d in data]

    # --- Periodos ---

    # NO DOCUMENTADO en OpenAPI
    def periodo(self, id: int, *, raw: bool = False) -> Periodo | dict[str, Any]:
        """Devuelve un periodo por id.

        Recurso ``PERIODO/{id}``.
        """
        data = self._backend.get_one(periodo_path(self._lang, id))
        if raw:
            return data
        return Periodo.model_validate(data)

    # --- Periodicidades ---

    def periodicidades(self, *, raw: bool = False) -> list[Periodicidad] | list[dict[str, Any]]:
        """Lista todas las periodicidades temporales.

        Recurso ``PERIODICIDADES``.
        """
        data = self._backend.get_list(periodicidades_path(self._lang))
        if raw:
            return data
        return [Periodicidad.model_validate(d) for d in data]

    # NO DOCUMENTADO en OpenAPI
    def periodicidad(self, id: int, *, raw: bool = False) -> Periodicidad | dict[str, Any]:
        """Devuelve una periodicidad por id.

        Recurso ``PERIODICIDAD/{id}``.
        """
        data = self._backend.get_one(periodicidad_path(self._lang, id))
        if raw:
            return data
        return Periodicidad.model_validate(data)

    # --- Clasificaciones ---

    def clasificaciones(self, *, raw: bool = False) -> list[Clasificacion] | list[dict[str, Any]]:
        """Lista todas las clasificaciones estadísticas.

        Recurso ``CLASIFICACIONES``.
        """
        data = self._backend.get_list(clasificaciones_path(self._lang))
        if raw:
            return data
        return [Clasificacion.model_validate(d) for d in data]

    def clasificaciones_operacion(
        self, op: str, *, raw: bool = False
    ) -> list[Clasificacion] | list[dict[str, Any]]:
        """Lista las clasificaciones de una operación.

        Recurso ``CLASIFICACIONES_OPERACION/{op}``.
        """
        data = self._backend.get_list(clasificaciones_operacion_path(self._lang, op))
        if raw:
            return data
        return [Clasificacion.model_validate(d) for d in data]


class AsyncMaestrosService(AsyncBaseService):
    """Espejo asíncrono de :class:`MaestrosService`."""

    # NO DOCUMENTADO en OpenAPI
    async def escalas(self, *, raw: bool = False) -> list[Escala] | list[dict[str, Any]]:
        """Lista todas las escalas numéricas (coroutine).

        Ver :meth:`MaestrosService.escalas`.
        """
        data = await self._backend.get_list(escalas_path(self._lang))
        if raw:
            return data
        return [Escala.model_validate(d) for d in data]

    # NO DOCUMENTADO en OpenAPI
    async def escala(self, id: int, *, raw: bool = False) -> Escala | dict[str, Any]:
        """Devuelve una escala por id (coroutine).

        Ver :meth:`MaestrosService.escala`.
        """
        data = await self._backend.get_one(escala_path(self._lang, id))
        if raw:
            return data
        return Escala.model_validate(data)

    # NO DOCUMENTADO en OpenAPI
    async def unidades(self, *, raw: bool = False) -> list[Unidad] | list[dict[str, Any]]:
        """Lista todas las unidades de medida (coroutine).

        Ver :meth:`MaestrosService.unidades`.
        """
        data = await self._backend.get_list(unidades_path(self._lang))
        if raw:
            return data
        return [Unidad.model_validate(d) for d in data]

    # NO DOCUMENTADO en OpenAPI
    async def unidad(self, id: int, *, raw: bool = False) -> Unidad | dict[str, Any]:
        """Devuelve una unidad por id (coroutine).

        Ver :meth:`MaestrosService.unidad`.
        """
        data = await self._backend.get_one(unidad_path(self._lang, id))
        if raw:
            return data
        return Unidad.model_validate(data)

    # NO DOCUMENTADO en OpenAPI
    async def unidades_operacion(
        self, op: str, *, raw: bool = False
    ) -> list[Unidad] | list[dict[str, Any]]:
        """Lista las unidades de una operación (coroutine).

        Ver :meth:`MaestrosService.unidades_operacion`.
        """
        data = await self._backend.get_list(unidades_operacion_path(self._lang, op))
        if raw:
            return data
        return [Unidad.model_validate(d) for d in data]

    # NO DOCUMENTADO en OpenAPI
    async def periodo(self, id: int, *, raw: bool = False) -> Periodo | dict[str, Any]:
        """Devuelve un periodo por id (coroutine).

        Ver :meth:`MaestrosService.periodo`.
        """
        data = await self._backend.get_one(periodo_path(self._lang, id))
        if raw:
            return data
        return Periodo.model_validate(data)

    async def periodicidades(
        self, *, raw: bool = False
    ) -> list[Periodicidad] | list[dict[str, Any]]:
        """Lista todas las periodicidades temporales (coroutine).

        Ver :meth:`MaestrosService.periodicidades`.
        """
        data = await self._backend.get_list(periodicidades_path(self._lang))
        if raw:
            return data
        return [Periodicidad.model_validate(d) for d in data]

    # NO DOCUMENTADO en OpenAPI
    async def periodicidad(self, id: int, *, raw: bool = False) -> Periodicidad | dict[str, Any]:
        """Devuelve una periodicidad por id (coroutine).

        Ver :meth:`MaestrosService.periodicidad`.
        """
        data = await self._backend.get_one(periodicidad_path(self._lang, id))
        if raw:
            return data
        return Periodicidad.model_validate(data)

    async def clasificaciones(
        self, *, raw: bool = False
    ) -> list[Clasificacion] | list[dict[str, Any]]:
        """Lista todas las clasificaciones estadísticas (coroutine).

        Ver :meth:`MaestrosService.clasificaciones`.
        """
        data = await self._backend.get_list(clasificaciones_path(self._lang))
        if raw:
            return data
        return [Clasificacion.model_validate(d) for d in data]

    async def clasificaciones_operacion(
        self, op: str, *, raw: bool = False
    ) -> list[Clasificacion] | list[dict[str, Any]]:
        """Lista las clasificaciones de una operación (coroutine).

        Ver :meth:`MaestrosService.clasificaciones_operacion`.
        """
        data = await self._backend.get_list(clasificaciones_operacion_path(self._lang, op))
        if raw:
            return data
        return [Clasificacion.model_validate(d) for d in data]
