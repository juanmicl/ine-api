# ine/services/datos.py
"""Servicio de datos (observaciones) de tablas, series y operaciones."""

from __future__ import annotations

from typing import Any

from ine._filters import Grupo, compilar_filtros
from ine._urls import (
    build_params,
    datos_metadataoperacion_path,
    datos_serie_path,
    datos_tabla_path,
)
from ine.models.datos import DatosSerie
from ine.services._base import AsyncBaseService, BaseService


class DatosService(BaseService):
    """Observaciones (datos) del INE."""

    def tabla(
        self,
        id: str,
        *,
        nult: int | None = None,
        det: str | None = None,
        tip: str | None = None,
        tv: list[str] | None = None,
        date: list[str] | None = None,
        raw: bool = False,
    ) -> list[DatosSerie] | list[dict[str, Any]]:
        """Devuelve los datos de una tabla.

        Recurso ``DATOS_TABLA/{id}``: observaciones de las series que componen
        la tabla indicada.

        Args:
            id: Identificador Tempus3 de la tabla (``Id``).
            nult: Devuelve los ``nult`` últimos datos o periodos.
            det: Nivel de detalle.
            tip: Tipo de respuesta.
            tv: Filtros ``id_variable:id_valor`` (repetibles).
            date: Rango ``aaaammdd:aaaammdd``; si se omite el final
                (``aaaammdd:``) se usa hasta el fin de la serie.
            raw: Si ``True``, devuelve ``list[dict]`` crudo.

        Returns:
            ``list[DatosSerie]`` por defecto, o ``list[dict]`` si ``raw=True``.
        """
        data = self._backend.get_list(
            datos_tabla_path(self._lang, id),
            build_params(nult=nult, det=det, tip=tip, tv=tv, date=date),
        )
        if raw:
            return data
        return [DatosSerie.model_validate(d) for d in data]

    def serie(
        self,
        id: str,
        *,
        nult: int | None = None,
        det: str | None = None,
        tip: str | None = None,
        date: list[str] | None = None,
        raw: bool = False,
    ) -> list[DatosSerie] | list[dict[str, Any]]:
        """Devuelve las observaciones (datos) de una serie.

        Recurso ``DATOS_SERIE/{id}``: valores temporales de la serie, con
        filtros opcionales de detalle, tipo, últimos periodos y rango de fechas.

        Args:
            id: Identificador Tempus3 de la serie (``Id``).
            nult: Devuelve los ``nult`` últimos datos o periodos.
            det: Nivel de detalle.
            tip: Tipo de respuesta.
            date: Rango ``aaaammdd:aaaammdd``.
            raw: Si ``True``, devuelve ``list[dict]`` crudo.

        Returns:
            ``list[DatosSerie]`` por defecto, o ``list[dict]`` si ``raw=True``.
        """
        data = self._backend.get_list(
            datos_serie_path(self._lang, id),
            build_params(nult=nult, det=det, tip=tip, date=date),
        )
        if raw:
            return data
        return [DatosSerie.model_validate(d) for d in data]

    def metadata_operacion(
        self,
        op: str,
        *,
        p: str | None = None,
        nult: int | None = None,
        det: str | None = None,
        tip: str | None = None,
        filtros: list[Grupo] | None = None,
        raw: bool = False,
    ) -> list[DatosSerie] | list[dict[str, Any]]:
        """Datos de una operación por metadatos (con filtros ``g``).

        Recurso ``DATOS_METADATAOPERACION/{op}``: observaciones de la operación
        permitiendo filtrar por periodicidad, últimos periodos y combinaciones
        OR/AND de variables mediante :data:`~ine._filters.Grupo`.

        Args:
            op: Identificador de la operación: ``Id``, ``Codigo`` o ``IOEXXXX``.
            p: Periodicidad: ``"1"`` mensual, ``"3"`` trimestral, ``"6"``
                bianual, ``"12"`` anual.
            nult: Devuelve los ``nult`` últimos datos o periodos.
            det: Nivel de detalle.
            tip: Tipo de respuesta.
            filtros: Filtros OR/AND: varias condiciones en un mismo
                :data:`~ine._filters.Grupo` = OR; grupos distintos = AND. Se
                compilan al parámetro ``g`` del INE.
            raw: Si ``True``, devuelve ``list[dict]`` crudo.

        Returns:
            ``list[DatosSerie]`` por defecto, o ``list[dict]`` si ``raw=True``.
        """
        params = build_params(p=p, nult=nult, det=det, tip=tip)
        if filtros is not None:
            params |= compilar_filtros(filtros)
        data = self._backend.get_list(
            datos_metadataoperacion_path(self._lang, op),
            params,
        )
        if raw:
            return data
        return [DatosSerie.model_validate(d) for d in data]


class AsyncDatosService(AsyncBaseService):
    """Espejo asíncrono de :class:`DatosService`."""

    async def tabla(
        self,
        id: str,
        *,
        nult: int | None = None,
        det: str | None = None,
        tip: str | None = None,
        tv: list[str] | None = None,
        date: list[str] | None = None,
        raw: bool = False,
    ) -> list[DatosSerie] | list[dict[str, Any]]:
        """Devuelve los datos de una tabla (coroutine).

        Ver :meth:`DatosService.tabla`.
        """
        data = await self._backend.get_list(
            datos_tabla_path(self._lang, id),
            build_params(nult=nult, det=det, tip=tip, tv=tv, date=date),
        )
        if raw:
            return data
        return [DatosSerie.model_validate(d) for d in data]

    async def serie(
        self,
        id: str,
        *,
        nult: int | None = None,
        det: str | None = None,
        tip: str | None = None,
        date: list[str] | None = None,
        raw: bool = False,
    ) -> list[DatosSerie] | list[dict[str, Any]]:
        """Devuelve las observaciones de una serie (coroutine).

        Ver :meth:`DatosService.serie`.
        """
        data = await self._backend.get_list(
            datos_serie_path(self._lang, id),
            build_params(nult=nult, det=det, tip=tip, date=date),
        )
        if raw:
            return data
        return [DatosSerie.model_validate(d) for d in data]

    async def metadata_operacion(
        self,
        op: str,
        *,
        p: str | None = None,
        nult: int | None = None,
        det: str | None = None,
        tip: str | None = None,
        filtros: list[Grupo] | None = None,
        raw: bool = False,
    ) -> list[DatosSerie] | list[dict[str, Any]]:
        """Datos de una operación por metadatos (coroutine).

        Ver :meth:`DatosService.metadata_operacion`.
        """
        params = build_params(p=p, nult=nult, det=det, tip=tip)
        if filtros is not None:
            params |= compilar_filtros(filtros)
        data = await self._backend.get_list(
            datos_metadataoperacion_path(self._lang, op),
            params,
        )
        if raw:
            return data
        return [DatosSerie.model_validate(d) for d in data]
