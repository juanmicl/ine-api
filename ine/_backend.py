# ine/_backend.py
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, overload

import httpx
from httpx_retries import Retry, RetryTransport

from ine._cache import Cache
from ine._config import Config
from ine.errors import (
    INEConnectionError,
    INEHTTPError,
    INELogicalError,
    INENotFoundError,
    INEParseError,
)

# Política de reintento: sólo GET idempotente, sobre errores de red + 429 + 5xx,
# respetando Retry-After. backoff exponencial (factor 0.5) con jitter completo
# (default de la librería). El rango 500-599 cubre todo el bloque 5xx.
_RETRY_STATUS_FORCELIST: tuple[int, ...] = (429, *range(500, 600))


def _build_retry(total: int) -> Retry:
    """Construye la política de reintentos a partir de ``config.retries``.

    Sólo se reintenta GET (único verbo que usa este Backend), sobre errores de
    red (defaults de la librería: Timeout/Network/RemoteProtocol) y los códigos
    429 + 5xx. Se respeta la cabecera Retry-After.
    """
    return Retry(
        total=total,
        allowed_methods=("GET",),
        status_forcelist=_RETRY_STATUS_FORCELIST,
        backoff_factor=0.5,
        respect_retry_after_header=True,
    )


@overload
def _maybe_retry_transport(
    config: Config, transport: httpx.BaseTransport
) -> httpx.BaseTransport: ...


@overload
def _maybe_retry_transport(
    config: Config, transport: httpx.AsyncBaseTransport
) -> httpx.AsyncBaseTransport: ...


def _maybe_retry_transport(
    config: Config,
    transport: httpx.BaseTransport | httpx.AsyncBaseTransport,
) -> httpx.BaseTransport | httpx.AsyncBaseTransport:
    """Envuelve ``transport`` con un :class:`RetryTransport` si ``config.retries>0``.

    Usado sólo cuando el Backend construye su propio cliente; un cliente
    inyectado (DI) no se toca. ``RetryTransport`` implementa a la vez
    ``BaseTransport`` y ``AsyncBaseTransport``, de ahí los overloads.
    """
    if config.retries > 0:
        return RetryTransport(transport=transport, retry=_build_retry(config.retries))
    return transport


class Backend:
    """Costura I/O sincrona. Único punto que sabe de httpx."""

    def __init__(
        self,
        config: Config,
        httpx_client: httpx.Client | None = None,
        cache: Cache | None = None,
    ) -> None:
        self._config = config
        self._cache = cache
        if httpx_client is None:
            transport = _maybe_retry_transport(config, httpx.HTTPTransport())
            httpx_client = httpx.Client(
                base_url=config.base_url,
                timeout=config.timeout,
                follow_redirects=config.follow_redirects,
                transport=transport,
                headers={"User-Agent": config.user_agent, **dict(config.headers)},
            )
        self._client = httpx_client

    def _request(
        self, path: str, params: Mapping[str, Any] | None = None
    ) -> list[Any] | dict[str, Any]:
        """I/O compartido: raise_for_status, guarda JSON, traduce errores (H1/H2/H3)."""
        try:
            response = self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            # Seguro: el Backend usa su propio `_raise_for_status` (nunca
            # httpx `response.raise_for_status()`), así que un HTTPStatusError
            # 4xx/5xx nunca escapa de `_client.get(...)`: todo lo que llega
            # aquí es genuinamente un error de conexión/transporte.
            raise INEConnectionError(str(exc)) from exc
        self._raise_for_status(response)
        self._guard_json(response)
        # La API devuelve list/dict en éxito, o str (mensaje de error lógico, H1).
        # Un 200 con cuerpo vacío/malformado escapa como JSONDecodeError: lo
        # traducimos a INEParseError para no romper el contrato (sólo ine.errors.*).
        try:
            data: list[Any] | dict[str, Any] | str = response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise INEParseError(f"Respuesta JSON inválida o vacía: {exc}") from exc
        if isinstance(data, str):
            raise INELogicalError(data)
        return data

    def _cached_request(
        self, path: str, params: Mapping[str, Any] | None = None
    ) -> list[Any] | dict[str, Any]:
        """Cachea éxitos por ``(path, params)``; los ``INEError`` se propagan sin cachear."""
        if self._cache is None:
            return self._request(path, params)
        key = (path, json.dumps(params or {}, sort_keys=True, default=str))
        hit: list[Any] | dict[str, Any] | None = self._cache.get(key)
        if hit is not None:
            return hit
        data = self._request(path, params)
        self._cache.set(key, data)
        return data

    def get_list(self, path: str, params: Mapping[str, Any] | None = None) -> list[Any]:
        """Para endpoints que devuelven un array JSON."""
        data = self._cached_request(path, params)
        if not isinstance(data, list):
            raise INEParseError(f"Se esperaba una lista en {path}, se obtuvo {type(data).__name__}")
        return data

    def get_one(self, path: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Para endpoints que devuelven un único objeto JSON."""
        data = self._cached_request(path, params)
        if not isinstance(data, dict):
            raise INEParseError(f"Se esperaba un objeto en {path}, se obtuvo {type(data).__name__}")
        return data

    def close(self) -> None:
        self._client.close()

    @staticmethod
    def _guard_json(response: httpx.Response) -> None:
        ctype = response.headers.get("content-type", "")
        if "application/json" not in ctype:
            raise INEParseError(
                f"Respuesta no JSON (content-type={ctype!r}): {response.text[:200]}"
            )

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.is_success:
            return
        url = str(response.request.url)
        body = response.text
        if response.status_code == 404:
            raise INENotFoundError(status=404, url=url, body=body)
        raise INEHTTPError(status=response.status_code, url=url, body=body)


class AsyncBackend:
    """Costura I/O asincrona. Único punto que sabe de ``httpx.AsyncClient``.

    Espejo de :class:`Backend`: misma lógica H1/H2/H3 y mismos *guards* de forma.
    Las diferencias son el mínimo sincrono/asincrono (``await`` en ``_client.get``
    y ``aclose``); los *helpers* estáticos se reutilizan desde :class:`Backend`.
    """

    def __init__(
        self,
        config: Config,
        httpx_client: httpx.AsyncClient | None = None,
        cache: Cache | None = None,
    ) -> None:
        self._config = config
        self._cache = cache
        if httpx_client is None:
            transport = _maybe_retry_transport(config, httpx.AsyncHTTPTransport())
            httpx_client = httpx.AsyncClient(
                base_url=config.base_url,
                timeout=config.timeout,
                follow_redirects=config.follow_redirects,
                transport=transport,
                headers={"User-Agent": config.user_agent, **dict(config.headers)},
            )
        self._client = httpx_client

    async def _request(
        self, path: str, params: Mapping[str, Any] | None = None
    ) -> list[Any] | dict[str, Any]:
        """I/O compartido: raise_for_status, guarda JSON, traduce errores (H1/H2/H3)."""
        try:
            response = await self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            # Seguro: el Backend usa su propio `_raise_for_status` (nunca
            # httpx `response.raise_for_status()`), así que un HTTPStatusError
            # 4xx/5xx nunca escapa de `_client.get(...)`: todo lo que llega
            # aquí es genuinamente un error de conexión/transporte.
            raise INEConnectionError(str(exc)) from exc
        Backend._raise_for_status(response)
        Backend._guard_json(response)
        # La API devuelve list/dict en éxito, o str (mensaje de error lógico, H1).
        # Un 200 con cuerpo vacío/malformado escapa como JSONDecodeError: lo
        # traducimos a INEParseError para no romper el contrato (sólo ine.errors.*).
        try:
            data: list[Any] | dict[str, Any] | str = response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise INEParseError(f"Respuesta JSON inválida o vacía: {exc}") from exc
        if isinstance(data, str):
            raise INELogicalError(data)
        return data

    async def _cached_request(
        self, path: str, params: Mapping[str, Any] | None = None
    ) -> list[Any] | dict[str, Any]:
        """Cachea éxitos por ``(path, params)``; los ``INEError`` se propagan sin cachear."""
        if self._cache is None:
            return await self._request(path, params)
        key = (path, json.dumps(params or {}, sort_keys=True, default=str))
        hit: list[Any] | dict[str, Any] | None = self._cache.get(key)
        if hit is not None:
            return hit
        data = await self._request(path, params)
        self._cache.set(key, data)
        return data

    async def get_list(self, path: str, params: Mapping[str, Any] | None = None) -> list[Any]:
        """Para endpoints que devuelven un array JSON."""
        data = await self._cached_request(path, params)
        if not isinstance(data, list):
            raise INEParseError(f"Se esperaba una lista en {path}, se obtuvo {type(data).__name__}")
        return data

    async def get_one(self, path: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Para endpoints que devuelven un único objeto JSON."""
        data = await self._cached_request(path, params)
        if not isinstance(data, dict):
            raise INEParseError(f"Se esperaba un objeto en {path}, se obtuvo {type(data).__name__}")
        return data

    async def aclose(self) -> None:
        await self._client.aclose()
