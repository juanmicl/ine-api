# ine/async_client.py
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from ine._backend import AsyncBackend
from ine._config import Config
from ine._config import Lang as Lang
from ine._urls import datos_tabla_path, operaciones_path, tablas_operacion_path
from ine.models.datos import DatosSerie
from ine.models.operaciones import Operacion


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
        httpx_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._config = Config(
            lang=lang,
            base_url=base_url,
            timeout=timeout,
            follow_redirects=follow_redirects,
            headers=headers or {},
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
