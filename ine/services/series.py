# ine/services/series.py
"""Servicio de series temporales: metadatos, catálogos y valores."""

from __future__ import annotations

from typing import Any

from ine._filters import Grupo, compilar_filtros
from ine._urls import (
    build_params,
    serie_metadataoperacion_path,
    serie_path,
    series_operacion_path,
    series_tabla_path,
    valores_serie_path,
)
from ine.models.series import Serie, Valor
from ine.services._base import AsyncBaseService, BaseService


class SeriesService(BaseService):
    """Series temporales del INE."""

    def get(
        self,
        id: str,
        *,
        det: str | None = None,
        tip: str | None = None,
        raw: bool = False,
    ) -> list[Serie] | list[dict[str, Any]]:
        """Devuelve los metadatos de una serie.

        Recurso ``SERIE/{id}``: ficha de la serie (código, nombre, decimales,
        operación, periodicidad...). El INE entrega siempre una lista.

        Args:
            id: Identificador Tempus3 de la serie (``Id``).
            det: Nivel de detalle: ``"0"`` básico, ``"1"`` detallado,
                ``"2"`` muy detallado.
            tip: Tipo de respuesta: ``"A"`` amigable, ``"M"`` con metadatos,
                ``"AM"`` ambos.
            raw: Si ``True``, devuelve ``list[dict]`` con los datos crudos del
                INE sin validar contra :class:`~ine.models.series.Serie`.

        Returns:
            ``list[Serie]`` por defecto, o ``list[dict]`` si ``raw=True``.
        """
        data = self._backend.get_list(
            serie_path(self._lang, id),
            build_params(det=det, tip=tip),
        )
        if raw:
            return data
        return [Serie.model_validate(d) for d in data]

    def by_operacion(
        self,
        op: str,
        *,
        det: str | None = None,
        tip: str | None = None,
        page: int | None = None,
        raw: bool = False,
    ) -> list[Serie] | list[dict[str, Any]]:
        """Lista las series de una operación.

        Recurso ``SERIES_OPERACION/{op}``: catálogo de series publicadas bajo
        la operación indicada, paginado (hasta 500 elementos por página).

        Args:
            op: Identificador de la operación: ``Id``, ``Codigo`` o ``IOEXXXX``.
            det: Nivel de detalle.
            tip: Tipo de respuesta.
            page: Número de página (el INE devuelve hasta 500 por página).
            raw: Si ``True``, devuelve ``list[dict]`` crudo.

        Returns:
            ``list[Serie]`` por defecto, o ``list[dict]`` si ``raw=True``.
        """
        data = self._backend.get_list(
            series_operacion_path(self._lang, op),
            build_params(det=det, tip=tip, page=page),
        )
        if raw:
            return data
        return [Serie.model_validate(d) for d in data]

    def by_tabla(
        self,
        id: str,
        *,
        det: str | None = None,
        tip: str | None = None,
        tv: list[str] | None = None,
        raw: bool = False,
    ) -> list[Serie] | list[dict[str, Any]]:
        """Lista las series que componen una tabla.

        Recurso ``SERIES_TABLA/{id}``: series individuales incluidas en la
        tabla indicada, con filtros opcionales por variable/valor.

        Args:
            id: Identificador Tempus3 de la tabla (``Id``).
            det: Nivel de detalle.
            tip: Tipo de respuesta.
            tv: Filtros ``id_variable:id_valor`` (repetibles).
            raw: Si ``True``, devuelve ``list[dict]`` crudo.

        Returns:
            ``list[Serie]`` por defecto, o ``list[dict]`` si ``raw=True``.
        """
        data = self._backend.get_list(
            series_tabla_path(self._lang, id),
            build_params(det=det, tip=tip, tv=tv),
        )
        if raw:
            return data
        return [Serie.model_validate(d) for d in data]

    def valores(
        self, id: str, *, det: str | None = None, raw: bool = False
    ) -> list[Valor] | list[dict[str, Any]]:
        """Devuelve los valores de las variables de una serie.

        Recurso ``VALORES_SERIE/{id}``: para cada variable que define la serie,
        los valores (categorías) que toma. Útil para construir los filtros
        ``tv`` / ``g`` de otras llamadas.

        Args:
            id: Identificador Tempus3 de la serie (``Id``).
            det: Nivel de detalle.
            raw: Si ``True``, devuelve ``list[dict]`` crudo.

        Returns:
            ``list[Valor]`` por defecto, o ``list[dict]`` si ``raw=True``.
        """
        data = self._backend.get_list(
            valores_serie_path(self._lang, id),
            build_params(det=det),
        )
        if raw:
            return data
        return [Valor.model_validate(d) for d in data]

    def metadata_operacion(
        self,
        op: str,
        *,
        p: str | None = None,
        det: str | None = None,
        tip: str | None = None,
        filtros: list[Grupo] | None = None,
        raw: bool = False,
    ) -> list[Serie] | list[dict[str, Any]]:
        """Series de una operación por metadatos (con filtros ``g``).

        Recurso ``SERIE_METADATAOPERACION/{op}``: catálogo de series de la
        operación permitiendo filtrar por periodicidad y combinaciones OR/AND de
        variables mediante :data:`~ine._filters.Grupo`.

        Args:
            op: Identificador de la operación: ``Id``, ``Codigo`` o ``IOEXXXX``.
            p: Periodicidad: ``"1"`` mensual, ``"3"`` trimestral, ``"6"``
                bianual, ``"12"`` anual.
            det: Nivel de detalle.
            tip: Tipo de respuesta.
            filtros: Filtros OR/AND: varias condiciones en un mismo
                :data:`~ine._filters.Grupo` = OR; grupos distintos = AND. Se
                compilan al parámetro ``g`` del INE.
            raw: Si ``True``, devuelve ``list[dict]`` crudo.

        Returns:
            ``list[Serie]`` por defecto, o ``list[dict]`` si ``raw=True``.
        """
        params = build_params(p=p, det=det, tip=tip)
        if filtros is not None:
            params |= compilar_filtros(filtros)
        data = self._backend.get_list(
            serie_metadataoperacion_path(self._lang, op),
            params,
        )
        if raw:
            return data
        return [Serie.model_validate(d) for d in data]


class AsyncSeriesService(AsyncBaseService):
    """Espejo asíncrono de :class:`SeriesService`."""

    async def get(
        self,
        id: str,
        *,
        det: str | None = None,
        tip: str | None = None,
        raw: bool = False,
    ) -> list[Serie] | list[dict[str, Any]]:
        """Devuelve los metadatos de una serie (coroutine).

        Ver :meth:`SeriesService.get`.
        """
        data = await self._backend.get_list(
            serie_path(self._lang, id),
            build_params(det=det, tip=tip),
        )
        if raw:
            return data
        return [Serie.model_validate(d) for d in data]

    async def by_operacion(
        self,
        op: str,
        *,
        det: str | None = None,
        tip: str | None = None,
        page: int | None = None,
        raw: bool = False,
    ) -> list[Serie] | list[dict[str, Any]]:
        """Lista las series de una operación (coroutine).

        Ver :meth:`SeriesService.by_operacion`.
        """
        data = await self._backend.get_list(
            series_operacion_path(self._lang, op),
            build_params(det=det, tip=tip, page=page),
        )
        if raw:
            return data
        return [Serie.model_validate(d) for d in data]

    async def by_tabla(
        self,
        id: str,
        *,
        det: str | None = None,
        tip: str | None = None,
        tv: list[str] | None = None,
        raw: bool = False,
    ) -> list[Serie] | list[dict[str, Any]]:
        """Lista las series que componen una tabla (coroutine).

        Ver :meth:`SeriesService.by_tabla`.
        """
        data = await self._backend.get_list(
            series_tabla_path(self._lang, id),
            build_params(det=det, tip=tip, tv=tv),
        )
        if raw:
            return data
        return [Serie.model_validate(d) for d in data]

    async def valores(
        self, id: str, *, det: str | None = None, raw: bool = False
    ) -> list[Valor] | list[dict[str, Any]]:
        """Devuelve los valores de las variables de una serie (coroutine).

        Ver :meth:`SeriesService.valores`.
        """
        data = await self._backend.get_list(
            valores_serie_path(self._lang, id),
            build_params(det=det),
        )
        if raw:
            return data
        return [Valor.model_validate(d) for d in data]

    async def metadata_operacion(
        self,
        op: str,
        *,
        p: str | None = None,
        det: str | None = None,
        tip: str | None = None,
        filtros: list[Grupo] | None = None,
        raw: bool = False,
    ) -> list[Serie] | list[dict[str, Any]]:
        """Series de una operación por metadatos (coroutine).

        Ver :meth:`SeriesService.metadata_operacion`.
        """
        params = build_params(p=p, det=det, tip=tip)
        if filtros is not None:
            params |= compilar_filtros(filtros)
        data = await self._backend.get_list(
            serie_metadataoperacion_path(self._lang, op),
            params,
        )
        if raw:
            return data
        return [Serie.model_validate(d) for d in data]
