# ine/services/tablas.py
"""Servicio de tablas (vistas predefinidas) de una operación.

Abarca tres endpoints:

* ``TABLAS_OPERACION/{op}`` — tablas en que se publica una operación.
* ``GRUPOS_TABLA/{id_tabla}`` — grupos (filtros) de una tabla.
* ``VALORES_GRUPOSTABLA/{id_tabla}/{id_grupo}`` — valores de un grupo.
"""

from __future__ import annotations

from typing import Any

from ine._urls import (
    build_params,
    grupos_tabla_path,
    tablas_operacion_path,
    valores_grupostabla_path,
)
from ine.models.series import Valor
from ine.models.tablas import Grupo, Tabla
from ine.services._base import AsyncBaseService, BaseService


class TablasService(BaseService):
    """Tablas (vistas predefinidas) del INE."""

    def by_operacion(
        self,
        op: str,
        *,
        det: str | None = None,
        geo: str | None = None,
        tip: str | None = None,
        raw: bool = False,
    ) -> list[Tabla] | list[dict[str, Any]]:
        """Lista las tablas de una operación.

        Recurso ``TABLAS_OPERACION/{op}``: tablas (vistas predefinidas) en las
        que se publica la operación indicada.

        Args:
            op: Identificador de la operación: ``Id`` o ``Codigo`` Tempus3, o
                el código ``IOEXXXX`` del INE.
            det: Nivel de detalle.
            geo: Ámbito geográfico.
            tip: Tipo de respuesta.
            raw: Si ``True``, devuelve ``list[dict]`` crudo.

        Returns:
            ``list[Tabla]`` por defecto; ``list[dict]`` si ``raw=True``.
        """
        data = self._backend.get_list(
            tablas_operacion_path(self._lang, op),
            build_params(det=det, geo=geo, tip=tip),
        )
        if raw:
            return data
        return [Tabla.model_validate(d) for d in data]

    def grupos(
        self,
        id_tabla: str,
        *,
        raw: bool = False,
    ) -> list[Grupo] | list[dict[str, Any]]:
        """Lista los grupos (filtros) de una tabla.

        Recurso ``GRUPOS_TABLA/{id_tabla}``.

        Args:
            id_tabla: Identificador Tempus3 de la tabla (``Id``).
            raw: Si ``True``, devuelve ``list[dict]`` crudo.

        Returns:
            ``list[Grupo]`` por defecto; ``list[dict]`` si ``raw=True``.
        """
        data = self._backend.get_list(grupos_tabla_path(self._lang, id_tabla))
        if raw:
            return data
        return [Grupo.model_validate(d) for d in data]

    def valores_grupo(
        self,
        id_tabla: str,
        id_grupo: int,
        *,
        det: str | None = None,
        raw: bool = False,
    ) -> list[Valor] | list[dict[str, Any]]:
        """Lista los valores de un grupo dentro de una tabla.

        Recurso ``VALORES_GRUPOSTABLA/{id_tabla}/{id_grupo}``.

        Args:
            id_tabla: Identificador Tempus3 de la tabla (``Id``).
            id_grupo: Identificador del grupo.
            det: Nivel de detalle.
            raw: Si ``True``, devuelve ``list[dict]`` crudo.

        Returns:
            ``list[Valor]`` por defecto; ``list[dict]`` si ``raw=True``.
        """
        data = self._backend.get_list(
            valores_grupostabla_path(self._lang, id_tabla, id_grupo),
            build_params(det=det),
        )
        if raw:
            return data
        return [Valor.model_validate(d) for d in data]


class AsyncTablasService(AsyncBaseService):
    """Espejo asíncrono de :class:`TablasService`."""

    async def by_operacion(
        self,
        op: str,
        *,
        det: str | None = None,
        geo: str | None = None,
        tip: str | None = None,
        raw: bool = False,
    ) -> list[Tabla] | list[dict[str, Any]]:
        """Lista las tablas de una operación (coroutine).

        Ver :meth:`TablasService.by_operacion`.
        """
        data = await self._backend.get_list(
            tablas_operacion_path(self._lang, op),
            build_params(det=det, geo=geo, tip=tip),
        )
        if raw:
            return data
        return [Tabla.model_validate(d) for d in data]

    async def grupos(
        self,
        id_tabla: str,
        *,
        raw: bool = False,
    ) -> list[Grupo] | list[dict[str, Any]]:
        """Lista los grupos de una tabla (coroutine).

        Ver :meth:`TablasService.grupos`.
        """
        data = await self._backend.get_list(grupos_tabla_path(self._lang, id_tabla))
        if raw:
            return data
        return [Grupo.model_validate(d) for d in data]

    async def valores_grupo(
        self,
        id_tabla: str,
        id_grupo: int,
        *,
        det: str | None = None,
        raw: bool = False,
    ) -> list[Valor] | list[dict[str, Any]]:
        """Lista los valores de un grupo de una tabla (coroutine).

        Ver :meth:`TablasService.valores_grupo`.
        """
        data = await self._backend.get_list(
            valores_grupostabla_path(self._lang, id_tabla, id_grupo),
            build_params(det=det),
        )
        if raw:
            return data
        return [Valor.model_validate(d) for d in data]
