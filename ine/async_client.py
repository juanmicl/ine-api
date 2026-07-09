# ine/async_client.py
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from ine._backend import AsyncBackend
from ine._config import Config
from ine._config import Lang as Lang
from ine._filters import Grupo, compilar_filtros
from ine._urls import (
    build_params,
    datos_metadataoperacion_path,
    datos_serie_path,
    datos_tabla_path,
    operacion_path,
    operaciones_path,
    serie_metadataoperacion_path,
    serie_path,
    series_operacion_path,
    series_tabla_path,
    tablas_operacion_path,
    valores_serie_path,
)
from ine.models.datos import DatosSerie
from ine.models.operaciones import Operacion
from ine.models.series import Serie, Valor


class AsyncClient:
    """Espejo asincrono de :class:`ine.client.Client`.

    Mismo constructor (keyword-only, DI de ``httpx.AsyncClient``), mismo ciclo de
    vida (``async with`` / ``aclose``) y mismos endpoints. Difiere sólo en el
    ``await`` y en reutilizar los *builders* de path de :mod:`ine._urls` (compartidos
    con el cliente sincrono a partir de la Fase 4).
    """

    def __init__(
        self,
        *,
        lang: Lang = Lang.ES,
        base_url: str = "https://servicios.ine.es",
        timeout: float = 10.0,
        follow_redirects: bool = True,
        headers: Mapping[str, str] | None = None,
        retries: int = 3,
        httpx_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._config = Config(
            lang=lang,
            base_url=base_url,
            timeout=timeout,
            follow_redirects=follow_redirects,
            headers=headers or {},
            retries=retries,
        )
        self._backend = AsyncBackend(self._config, httpx_client=httpx_client)

    # --- context manager ---
    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def close(self) -> None:
        await self._backend.aclose()

    # --- endpoints (espejo de Client) ---
    async def get_operaciones(self, *, raw: bool = False) -> list[Operacion] | list[dict[str, Any]]:
        data = await self._backend.get_list(operaciones_path(self._config.lang.value))
        if raw:
            return data
        return [Operacion.model_validate(d) for d in data]

    async def get_tablas(self, operacion: str) -> list[dict[str, Any]]:
        return await self._backend.get_list(
            tablas_operacion_path(self._config.lang.value, operacion)
        )

    async def get_datos_tabla(
        self, tabla_id: str, *, raw: bool = False
    ) -> list[DatosSerie] | list[dict[str, Any]]:
        data = await self._backend.get_list(datos_tabla_path(self._config.lang.value, tabla_id))
        if raw:
            return data
        return [DatosSerie.model_validate(d) for d in data]

    # --- OPERACION / DATOS (Fase 5) ---
    async def get_operacion(
        self, id: str, *, det: str | None = None, raw: bool = False
    ) -> list[Operacion] | list[dict[str, Any]]:
        data = await self._backend.get_list(
            operacion_path(self._config.lang.value, id),
            build_params(det=det),
        )
        if raw:
            return data
        return [Operacion.model_validate(d) for d in data]

    async def get_datos_serie(
        self,
        id_serie: str,
        *,
        nult: int | None = None,
        det: str | None = None,
        tip: str | None = None,
        date: list[str] | None = None,
        raw: bool = False,
    ) -> list[DatosSerie] | list[dict[str, Any]]:
        data = await self._backend.get_list(
            datos_serie_path(self._config.lang.value, id_serie),
            build_params(nult=nult, det=det, tip=tip, date=date),
        )
        if raw:
            return data
        return [DatosSerie.model_validate(d) for d in data]

    async def get_datos_metadataoperacion(
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
        params = build_params(p=p, nult=nult, det=det, tip=tip)
        if filtros is not None:
            params |= compilar_filtros(filtros)
        data = await self._backend.get_list(
            datos_metadataoperacion_path(self._config.lang.value, op),
            params,
        )
        if raw:
            return data
        return [DatosSerie.model_validate(d) for d in data]

    # --- SERIES (Fase 5) ---
    async def get_serie(
        self,
        id_serie: str,
        *,
        det: str | None = None,
        tip: str | None = None,
        raw: bool = False,
    ) -> list[Serie] | list[dict[str, Any]]:
        data = await self._backend.get_list(
            serie_path(self._config.lang.value, id_serie),
            build_params(det=det, tip=tip),
        )
        if raw:
            return data
        return [Serie.model_validate(d) for d in data]

    async def get_series_operacion(
        self,
        op: str,
        *,
        det: str | None = None,
        tip: str | None = None,
        page: int | None = None,
        raw: bool = False,
    ) -> list[Serie] | list[dict[str, Any]]:
        data = await self._backend.get_list(
            series_operacion_path(self._config.lang.value, op),
            build_params(det=det, tip=tip, page=page),
        )
        if raw:
            return data
        return [Serie.model_validate(d) for d in data]

    async def get_series_tabla(
        self,
        id_tabla: str,
        *,
        det: str | None = None,
        tip: str | None = None,
        tv: list[str] | None = None,
        raw: bool = False,
    ) -> list[Serie] | list[dict[str, Any]]:
        data = await self._backend.get_list(
            series_tabla_path(self._config.lang.value, id_tabla),
            build_params(det=det, tip=tip, tv=tv),
        )
        if raw:
            return data
        return [Serie.model_validate(d) for d in data]

    async def get_valores_serie(
        self, id_serie: str, *, det: str | None = None, raw: bool = False
    ) -> list[Valor] | list[dict[str, Any]]:
        data = await self._backend.get_list(
            valores_serie_path(self._config.lang.value, id_serie),
            build_params(det=det),
        )
        if raw:
            return data
        return [Valor.model_validate(d) for d in data]

    async def get_series_metadata_operacion(
        self,
        op: str,
        *,
        p: str | None = None,
        det: str | None = None,
        tip: str | None = None,
        filtros: list[Grupo] | None = None,
        raw: bool = False,
    ) -> list[Serie] | list[dict[str, Any]]:
        params = build_params(p=p, det=det, tip=tip)
        if filtros is not None:
            params |= compilar_filtros(filtros)
        data = await self._backend.get_list(
            serie_metadataoperacion_path(self._config.lang.value, op),
            params,
        )
        if raw:
            return data
        return [Serie.model_validate(d) for d in data]
