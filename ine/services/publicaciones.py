# ine/services/publicaciones.py
"""Servicio de publicaciones del INE: catálogo y fechas de publicación."""

from __future__ import annotations

from typing import Any

from ine._urls import (
    build_params,
    publicacion_fecha_path,
    publicaciones_operacion_path,
    publicaciones_path,
)
from ine.models.publicaciones import Publicacion, PublicacionFecha
from ine.services._base import AsyncBaseService, BaseService


class PublicacionesService(BaseService):
    """Publicaciones estadísticas del INE."""

    def publicaciones(
        self, *, det: str | None = None, tip: str | None = None, raw: bool = False
    ) -> list[Publicacion] | list[dict[str, Any]]:
        """Lista todas las publicaciones.

        Recurso ``PUBLICACIONES``.
        """
        data = self._backend.get_list(
            publicaciones_path(self._lang),
            build_params(det=det, tip=tip),
        )
        if raw:
            return data
        return [Publicacion.model_validate(d) for d in data]

    def publicaciones_operacion(
        self, op: str, *, det: str | None = None, tip: str | None = None, raw: bool = False
    ) -> list[Publicacion] | list[dict[str, Any]]:
        """Lista las publicaciones de una operación.

        Recurso ``PUBLICACIONES_OPERACION/{op}``.
        """
        data = self._backend.get_list(
            publicaciones_operacion_path(self._lang, op),
            build_params(det=det, tip=tip),
        )
        if raw:
            return data
        return [Publicacion.model_validate(d) for d in data]

    def publicacion_fecha(
        self,
        id_publicacion: int,
        *,
        det: str | None = None,
        tip: str | None = None,
        raw: bool = False,
    ) -> list[PublicacionFecha] | list[dict[str, Any]]:
        """Lista las fechas/volúmenes de una publicación.

        Recurso ``PUBLICACIONFECHA_PUBLICACION/{id_publicacion}``.
        """
        data = self._backend.get_list(
            publicacion_fecha_path(self._lang, id_publicacion),
            build_params(det=det, tip=tip),
        )
        if raw:
            return data
        return [PublicacionFecha.model_validate(d) for d in data]


class AsyncPublicacionesService(AsyncBaseService):
    """Espejo asíncrono de :class:`PublicacionesService`."""

    async def publicaciones(
        self, *, det: str | None = None, tip: str | None = None, raw: bool = False
    ) -> list[Publicacion] | list[dict[str, Any]]:
        """Lista todas las publicaciones (coroutine).

        Ver :meth:`PublicacionesService.publicaciones`.
        """
        data = await self._backend.get_list(
            publicaciones_path(self._lang),
            build_params(det=det, tip=tip),
        )
        if raw:
            return data
        return [Publicacion.model_validate(d) for d in data]

    async def publicaciones_operacion(
        self, op: str, *, det: str | None = None, tip: str | None = None, raw: bool = False
    ) -> list[Publicacion] | list[dict[str, Any]]:
        """Lista las publicaciones de una operación (coroutine).

        Ver :meth:`PublicacionesService.publicaciones_operacion`.
        """
        data = await self._backend.get_list(
            publicaciones_operacion_path(self._lang, op),
            build_params(det=det, tip=tip),
        )
        if raw:
            return data
        return [Publicacion.model_validate(d) for d in data]

    async def publicacion_fecha(
        self,
        id_publicacion: int,
        *,
        det: str | None = None,
        tip: str | None = None,
        raw: bool = False,
    ) -> list[PublicacionFecha] | list[dict[str, Any]]:
        """Lista las fechas/volúmenes de una publicación (coroutine).

        Ver :meth:`PublicacionesService.publicacion_fecha`.
        """
        data = await self._backend.get_list(
            publicacion_fecha_path(self._lang, id_publicacion),
            build_params(det=det, tip=tip),
        )
        if raw:
            return data
        return [PublicacionFecha.model_validate(d) for d in data]
