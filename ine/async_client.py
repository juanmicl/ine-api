# ine/async_client.py
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import httpx

from ine._backend import AsyncBackend
from ine._cache import Cache
from ine._config import Config
from ine._config import Lang as Lang
from ine._files import Format, build_file_url
from ine.services import (
    AsyncDatosService,
    AsyncMaestrosService,
    AsyncOperacionesService,
    AsyncPublicacionesService,
    AsyncSeriesService,
    AsyncTablasService,
    AsyncVariablesService,
)


class AsyncClient:
    """Cliente asíncrono para la API Tempus del INE.

    Espejo asíncrono de :class:`~ine.client.Client`: misma API y mismos
    parámetros (todos *keyword-only*), sustituyendo :class:`httpx.Client` por
    :class:`httpx.AsyncClient`. Los endpoints se organizan en **namespaces por
    dominio** (coroutines a esperar con ``await``):

        async with AsyncClient() as c:
            ops = await c.operaciones.list()
            datos = await c.datos.serie("53262")

    La descarga de ficheros oficiales queda en la raíz:

        await c.download_table("68535", fmt=Format.CSV_BDSC)

    Inyección de dependencias: si se pasa ``httpx_client`` (un
    :class:`httpx.AsyncClient` ya configurado), el Backend lo reutiliza tal cual
    y no aplica su propia política de reintentos ni sus cabeceras por defecto —
    útil para tests o para configuración avanzada del transporte.

    Los errores de red y HTTP se traducen a la jerarquía
    :class:`~ine.errors.INEError` (ver :mod:`ine.errors`).
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
        cache: Cache | None = None,
    ) -> None:
        """Construye el cliente.

        Args:
            lang: Idioma de las respuestas (``Lang.ES`` por defecto).
            base_url: Base del servicio Tempus del INE.
            timeout: Timeout por petición, en segundos.
            follow_redirects: Si seguir redirecciones HTTP.
            headers: Cabeceras extra añadidas a cada petición.
            retries: Nº máx. de reintentos sobre GET idempotente (errores de
                red + 429 + 5xx). ``0`` los desactiva. Sólo aplica cuando el
                Backend crea su propio cliente; un ``httpx_client`` inyectado se
                respeta sin modificar.
            httpx_client: Cliente HTTP asíncrono inyectado (DI). Si se pasa, se
                reutiliza tal cual (sin reintentos ni cabeceras propias).
            cache: Cache en memoria opt-in (:class:`~ine._cache.Cache`). Si se
                pasa, los éxitos se cachean por ``(path, params)`` durante su
                ``ttl``; los errores no se cachean. ``None`` (default) = sin
                cache (comportamiento actual).

        Note:
            Todos los parámetros son *keyword-only*.
        """
        self._config = Config(
            lang=lang,
            base_url=base_url,
            timeout=timeout,
            follow_redirects=follow_redirects,
            headers=headers or {},
            retries=retries,
        )
        self._backend = AsyncBackend(self._config, httpx_client=httpx_client, cache=cache)
        # Servicios por dominio: cada uno encapsula un grupo de endpoints.
        self.operaciones = AsyncOperacionesService(self._backend, self._config)
        self.series = AsyncSeriesService(self._backend, self._config)
        self.datos = AsyncDatosService(self._backend, self._config)
        self.tablas = AsyncTablasService(self._backend, self._config)
        self.maestros = AsyncMaestrosService(self._backend, self._config)
        self.publicaciones = AsyncPublicacionesService(self._backend, self._config)
        self.variables = AsyncVariablesService(self._backend, self._config)

    # --- context manager ---
    async def __aenter__(self) -> AsyncClient:
        """Entra en el bloque ``async with`` y devuelve ``self``."""
        return self

    async def __aexit__(self, *exc: object) -> None:
        """Sale del bloque ``async with`` y cierra la conexión HTTP."""
        await self.close()

    async def close(self) -> None:
        """Cierra la conexión HTTP subyacente (idempotente).

        Note:
            Método coroutine: invocar con ``await``.
        """
        await self._backend.aclose()

    # --- ficheros (CSV / PC-Axis / XLSX) ---
    async def download_table(
        self,
        table_id: str,
        fmt: Format = Format.CSV_BDSC,
        *,
        path: str | Path | None = None,
        lang: str | None = None,
    ) -> Path | bytes:
        """Descarga el fichero oficial de una tabla (CSV / PC-Axis / XLSX).

        Servicio de ficheros del INE — host distinto a la API Tempus JSON:
        ``https://www.ine.es/jaxiT3/files/t/{lang}/{fmt}/{table_id}.{ext}?nocab=1``.
        Útil para tablas muy grandes que la API JSON rechaza por "restricciones
        de volumen" (p. ej. el Padrón, id 68535) o cuando se necesita el formato
        oficial. La descarga es por *streaming* (no se carga entera en memoria
        salvo que se pida explícitamente).

        Args:
            table_id: Identificador Tempus3 de la tabla (``Id``).
            fmt: Formato del fichero (:class:`Format`). Por defecto CSV (BDSC).
            path: Si se da (``str`` o :class:`~pathlib.Path`), streama por chunks
                al fichero y devuelve :class:`~pathlib.Path` — seguro para tablas
                de decenas de MB. Si es ``None`` (default), devuelve ``bytes`` en
                memoria (cuidado con tablas muy grandes).
            lang: Idioma del fichero; si es ``None`` usa el ``lang`` del cliente.

        Returns:
            :class:`~pathlib.Path` si se pasó ``path``; ``bytes`` en caso
            contrario. (No existe ``raw`` aquí: nunca se devuelven modelos.)

        Raises:
            INENotFoundError: La tabla no existe (HTTP 404).
            INEHTTPError: Otro error HTTP 4xx/5xx del servicio de ficheros.
            INEConnectionError: Error de red durante la descarga.

        Note:
            Método coroutine: invocar con ``await``.
        """
        url = build_file_url(lang or self._config.lang.value, fmt, table_id)
        if path is not None:
            with open(path, "wb") as f:
                async with self._backend.stream(url) as response:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
            return Path(path)
        async with self._backend.stream(url) as response:
            return await response.aread()
