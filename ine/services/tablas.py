# ine/services/tablas.py
"""Servicio de tablas (vistas predefinidas) de una operación."""

from __future__ import annotations

from typing import Any

from ine._urls import build_params, tablas_operacion_path
from ine.services._base import AsyncBaseService, BaseService


class TablasService(BaseService):
    """Tablas (vistas predefinidas) del INE.

    El INE no documenta un esquema estable para ``TABLAS_OPERACION``, por lo que
    siempre se devuelve ``list[dict]`` crudo (sin modelo).
    """

    def by_operacion(
        self,
        op: str,
        *,
        det: str | None = None,
        geo: str | None = None,
        tip: str | None = None,
        raw: bool = False,
    ) -> list[dict[str, Any]]:
        """Lista las tablas de una operación.

        Recurso ``TABLAS_OPERACION/{op}``: tablas (vistas predefinidas) en las
        que se publica la operación indicada.

        Args:
            op: Identificador de la operación: ``Id`` o ``Codigo`` Tempus3, o
                el código ``IOEXXXX`` del INE.
            det: Nivel de detalle.
            geo: Ámbito geográfico.
            tip: Tipo de respuesta.
            raw: Sin efecto (no existe modelo de Tabla; siempre se devuelven
                ``list[dict]``). Se acepta por simetría con el resto de servicios.

        Returns:
            Las tablas de la operación como ``list[dict]`` (sin modelo).
        """
        return self._backend.get_list(
            tablas_operacion_path(self._lang, op),
            build_params(det=det, geo=geo, tip=tip),
        )


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
    ) -> list[dict[str, Any]]:
        """Lista las tablas de una operación (coroutine).

        Ver :meth:`TablasService.by_operacion`.
        """
        return await self._backend.get_list(
            tablas_operacion_path(self._lang, op),
            build_params(det=det, geo=geo, tip=tip),
        )
