# ine/services/valores.py
"""Servicio de valores de variables del INE.

Reutiliza el modelo :class:`~ine.models.series.Valor` (no se duplica).
Nombres ``by_*`` / ``hijos`` por consistencia con el resto de servicios.
"""

from __future__ import annotations

from typing import Any

from ine._urls import (
    build_params,
    valores_hijos_path,
    valores_variable_operacion_path,
    valores_variable_path,
)
from ine.models.series import Valor
from ine.services._base import AsyncBaseService, BaseService


class ValoresService(BaseService):
    """Valores (categorías) de variables del INE."""

    def by_variable(
        self,
        id_variable: int,
        *,
        det: str | None = None,
        clasif: int | None = None,
        raw: bool = False,
    ) -> list[Valor] | list[dict[str, Any]]:
        """Lista los valores de una variable.

        Recurso ``VALORES_VARIABLE/{id_variable}``.
        """
        data = self._backend.get_list(
            valores_variable_path(self._lang, id_variable),
            build_params(det=det, clasif=clasif),
        )
        if raw:
            return data
        return [Valor.model_validate(d) for d in data]

    def by_variable_operacion(
        self,
        id_variable: int,
        op: str,
        *,
        det: str | None = None,
        raw: bool = False,
    ) -> list[Valor] | list[dict[str, Any]]:
        """Lista los valores de una variable en una operación.

        Recurso ``VALORES_VARIABLEOPERACION/{id_variable}/{op}``.
        """
        data = self._backend.get_list(
            valores_variable_operacion_path(self._lang, id_variable, op),
            build_params(det=det),
        )
        if raw:
            return data
        return [Valor.model_validate(d) for d in data]

    def hijos(
        self,
        id_variable: int,
        id_valor: int,
        *,
        det: str | None = None,
        raw: bool = False,
    ) -> list[Valor] | list[dict[str, Any]]:
        """Lista los valores hijos (subcategorías) de un valor.

        Recurso ``VALORES_HIJOS/{id_variable}/{id_valor}``.
        """
        data = self._backend.get_list(
            valores_hijos_path(self._lang, id_variable, id_valor),
            build_params(det=det),
        )
        if raw:
            return data
        return [Valor.model_validate(d) for d in data]


class AsyncValoresService(AsyncBaseService):
    """Espejo asíncrono de :class:`ValoresService`."""

    async def by_variable(
        self,
        id_variable: int,
        *,
        det: str | None = None,
        clasif: int | None = None,
        raw: bool = False,
    ) -> list[Valor] | list[dict[str, Any]]:
        """Lista los valores de una variable (coroutine).

        Ver :meth:`ValoresService.by_variable`.
        """
        data = await self._backend.get_list(
            valores_variable_path(self._lang, id_variable),
            build_params(det=det, clasif=clasif),
        )
        if raw:
            return data
        return [Valor.model_validate(d) for d in data]

    async def by_variable_operacion(
        self,
        id_variable: int,
        op: str,
        *,
        det: str | None = None,
        raw: bool = False,
    ) -> list[Valor] | list[dict[str, Any]]:
        """Lista los valores de una variable en una operación (coroutine).

        Ver :meth:`ValoresService.by_variable_operacion`.
        """
        data = await self._backend.get_list(
            valores_variable_operacion_path(self._lang, id_variable, op),
            build_params(det=det),
        )
        if raw:
            return data
        return [Valor.model_validate(d) for d in data]

    async def hijos(
        self,
        id_variable: int,
        id_valor: int,
        *,
        det: str | None = None,
        raw: bool = False,
    ) -> list[Valor] | list[dict[str, Any]]:
        """Lista los valores hijos de un valor (coroutine).

        Ver :meth:`ValoresService.hijos`.
        """
        data = await self._backend.get_list(
            valores_hijos_path(self._lang, id_variable, id_valor),
            build_params(det=det),
        )
        if raw:
            return data
        return [Valor.model_validate(d) for d in data]
