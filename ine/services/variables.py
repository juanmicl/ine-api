# ine/services/variables.py
"""Servicio de variables del INE: catálogo y ficha individual."""

from __future__ import annotations

from typing import Any

from ine._urls import (
    build_params,
    variable_path,
    variables_operacion_path,
    variables_path,
)
from ine.models.variables import Variable
from ine.services._base import AsyncBaseService, BaseService


class VariablesService(BaseService):
    """Variables del INE (dimensiones que estructuran las series)."""

    def variables(
        self, *, page: int | None = None, raw: bool = False
    ) -> list[Variable] | list[dict[str, Any]]:
        """Lista todas las variables (paginado).

        Recurso ``VARIABLES``.
        """
        data = self._backend.get_list(
            variables_path(self._lang),
            build_params(page=page),
        )
        if raw:
            return data
        return [Variable.model_validate(d) for d in data]

    def variables_operacion(
        self, op: str, *, page: int | None = None, raw: bool = False
    ) -> list[Variable] | list[dict[str, Any]]:
        """Lista las variables de una operación (paginado).

        Recurso ``VARIABLES_OPERACION/{op}``.
        """
        data = self._backend.get_list(
            variables_operacion_path(self._lang, op),
            build_params(page=page),
        )
        if raw:
            return data
        return [Variable.model_validate(d) for d in data]

    # NO DOCUMENTADO en OpenAPI
    def variable(self, id: int, *, raw: bool = False) -> Variable | dict[str, Any]:
        """Devuelve una variable por id.

        Recurso ``VARIABLE/{id}``.
        """
        data = self._backend.get_one(variable_path(self._lang, id))
        if raw:
            return data
        return Variable.model_validate(data)


class AsyncVariablesService(AsyncBaseService):
    """Espejo asíncrono de :class:`VariablesService`."""

    async def variables(
        self, *, page: int | None = None, raw: bool = False
    ) -> list[Variable] | list[dict[str, Any]]:
        """Lista todas las variables (paginado) (coroutine).

        Ver :meth:`VariablesService.variables`.
        """
        data = await self._backend.get_list(
            variables_path(self._lang),
            build_params(page=page),
        )
        if raw:
            return data
        return [Variable.model_validate(d) for d in data]

    async def variables_operacion(
        self, op: str, *, page: int | None = None, raw: bool = False
    ) -> list[Variable] | list[dict[str, Any]]:
        """Lista las variables de una operación (paginado) (coroutine).

        Ver :meth:`VariablesService.variables_operacion`.
        """
        data = await self._backend.get_list(
            variables_operacion_path(self._lang, op),
            build_params(page=page),
        )
        if raw:
            return data
        return [Variable.model_validate(d) for d in data]

    # NO DOCUMENTADO en OpenAPI
    async def variable(self, id: int, *, raw: bool = False) -> Variable | dict[str, Any]:
        """Devuelve una variable por id (coroutine).

        Ver :meth:`VariablesService.variable`.
        """
        data = await self._backend.get_one(variable_path(self._lang, id))
        if raw:
            return data
        return Variable.model_validate(data)
