# ine/services/operaciones.py
"""Servicio de operaciones estadísticas (catálogo y ficha)."""

from __future__ import annotations

from typing import Any, List

from ine._urls import build_params, operacion_path, operaciones_path
from ine.models.operaciones import Operacion
from ine.services._base import AsyncBaseService, BaseService


class OperacionesService(BaseService):
    """Operaciones estadísticas del INE (IPC, EPA, ...)."""

    def list(
        self,
        *,
        det: str | None = None,
        geo: str | None = None,
        page: int | None = None,
        raw: bool = False,
    ) -> List[Operacion] | List[dict[str, Any]]:
        """Lista las operaciones estadísticas disponibles.

        Recurso ``OPERACIONES_DISPONIBLES``: catálogo de operaciones sobre las
        que después se pueden pedir series, tablas y datos.

        Args:
            det: Nivel de detalle: ``"0"`` básico, ``"1"`` detallado,
                ``"2"`` muy detallado.
            geo: Ámbito geográfico.
            page: Número de página.
            raw: Si ``True``, devuelve ``list[dict]`` con los datos crudos del
                INE sin validar contra :class:`~ine.models.operaciones.Operacion`.

        Returns:
            ``list[Operacion]`` por defecto, o ``list[dict]`` si ``raw=True``.
        """
        data = self._backend.get_list(
            operaciones_path(self._lang),
            build_params(det=det, geo=geo, page=page),
        )
        if raw:
            return data
        return [Operacion.model_validate(d) for d in data]

    def get(
        self, id: str, *, det: str | None = None, raw: bool = False
    ) -> List[Operacion] | List[dict[str, Any]]:
        """Devuelve los metadatos de una operación.

        Recurso ``OPERACION/{id}``: ficha de la operación (nombre, código,
        IOE...). El INE entrega siempre una lista (habitualmente de un elemento).

        Args:
            id: Identificador de la operación: ``Id``, ``Codigo`` o ``IOEXXXX``.
            det: Nivel de detalle: ``"0"`` básico, ``"1"`` detallado,
                ``"2"`` muy detallado.
            raw: Si ``True``, devuelve ``list[dict]`` con los datos crudos del
                INE sin validar contra :class:`~ine.models.operaciones.Operacion`.

        Returns:
            ``list[Operacion]`` por defecto, o ``list[dict]`` si ``raw=True``.
        """
        data = self._backend.get_list(
            operacion_path(self._lang, id),
            build_params(det=det),
        )
        if raw:
            return data
        return [Operacion.model_validate(d) for d in data]


class AsyncOperacionesService(AsyncBaseService):
    """Espejo asíncrono de :class:`OperacionesService`."""

    async def list(
        self,
        *,
        det: str | None = None,
        geo: str | None = None,
        page: int | None = None,
        raw: bool = False,
    ) -> List[Operacion] | List[dict[str, Any]]:
        """Lista las operaciones estadísticas disponibles (coroutine).

        Ver :meth:`OperacionesService.list`.
        """
        data = await self._backend.get_list(
            operaciones_path(self._lang),
            build_params(det=det, geo=geo, page=page),
        )
        if raw:
            return data
        return [Operacion.model_validate(d) for d in data]

    async def get(
        self, id: str, *, det: str | None = None, raw: bool = False
    ) -> List[Operacion] | List[dict[str, Any]]:
        """Devuelve los metadatos de una operación (coroutine).

        Ver :meth:`OperacionesService.get`.
        """
        data = await self._backend.get_list(
            operacion_path(self._lang, id),
            build_params(det=det),
        )
        if raw:
            return data
        return [Operacion.model_validate(d) for d in data]
