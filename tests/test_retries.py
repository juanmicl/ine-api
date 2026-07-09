# tests/test_retries.py
#
# Estrategia de test (ver nota en task-5.1-report.md):
#   Los tests comportamentales usan respx con `side_effect` que lanza excepciones
#   reales de httpx (p.ej. ConnectError) o respuestas 429/5xx. RetryTransport
#   envuelve el httpx.HTTPTransport/AsyncHTTPTransport interno; respx intercepta
#   `handle_request`/`handle_async_request` de esos transportes, por lo que el
#   reintento del RetryTransport vuelve a golpear el mock de respx y el conteo de
#   `route.call_count` refleja los reintentos reales.
#
#   Además de los tests comportamentales, hay tests de construcción que inspeccionan
#   `backend._client._transport` para garantizar que:
#     - retries>0  -> se instala un RetryTransport,
#     - retries=0  -> NO se instala,
#     - cliente inyectado (DI) -> NO se envuelve (el usuario es dueño de su cliente).
#
#   Los sleeps del backoff se neutralizan con un fixture autouse (monkeypatch de
#   Retry.sleep / Retry.asleep) para mantener los tests rápidos y deterministas.
from __future__ import annotations

import httpx
import pytest
import respx
from httpx_retries import Retry, RetryTransport

from ine._backend import AsyncBackend, Backend
from ine._config import Config
from ine.errors import INEConnectionError, INEHTTPError

_URL = "https://servicios.ine.es/wstempus/js/ES/X"
_PATH = "/wstempus/js/ES/X"


@pytest.fixture(autouse=True)
def _no_retry_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Evita sleeps reales de backoff: hace los tests instantáneos y deterministas."""

    monkeypatch.setattr(Retry, "sleep", lambda self, response: None)

    async def _async_noop(self: Retry, response: object) -> None:
        return None

    monkeypatch.setattr(Retry, "asleep", _async_noop)


# ---------------------------------------------------------------- behavioral sync


@respx.mock
def test_sync_retries_network_error_then_succeeds():
    """Dos ConnectError y luego 200 -> reintenta y devuelve el dato (3 llamadas)."""
    route = respx.get(_URL).mock(
        side_effect=[
            httpx.ConnectError("boom1"),
            httpx.ConnectError("boom2"),
            httpx.Response(200, json=[]),
        ]
    )
    data = Backend(Config(retries=3)).get_list(_PATH)
    assert data == []
    assert route.call_count == 3


@respx.mock
def test_sync_retries_429_then_succeeds():
    """Un 429 (con Retry-After=0) y luego 200 -> reintenta por código de estado."""
    route = respx.get(_URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json=[{"Id": 1}]),
        ]
    )
    data = Backend(Config(retries=3)).get_list(_PATH)
    assert data == [{"Id": 1}]
    assert route.call_count == 2


@respx.mock
def test_sync_retries_5xx_exhausted_raises_http_error():
    """500 persistente -> agota 3 reintentos (4 intentos totales) y traduce a INEHTTPError."""
    route = respx.get(_URL).mock(return_value=httpx.Response(500, text="err"))
    backend = Backend(Config(retries=3))
    with pytest.raises(INEHTTPError) as exc:
        backend.get_list(_PATH)
    assert not isinstance(exc.value, INEConnectionError)
    assert route.call_count == 4  # 1 intento + 3 reintentos


@respx.mock
def test_sync_network_error_exhausted_raises_connection_error():
    """ConnectError persistente -> agota reintentos y traduce a INEConnectionError."""
    route = respx.get(_URL).mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(INEConnectionError):
        Backend(Config(retries=3)).get_list(_PATH)
    assert route.call_count == 4


# -------------------------------------------------------------- behavioral async


@respx.mock
@pytest.mark.anyio
async def test_async_retries_network_error_then_succeeds():
    """Espejo asincrono: dos ConnectError y luego 200."""
    route = respx.get(_URL).mock(
        side_effect=[
            httpx.ConnectError("boom1"),
            httpx.ConnectError("boom2"),
            httpx.Response(200, json=[]),
        ]
    )
    data = await AsyncBackend(Config(retries=3)).get_list(_PATH)
    assert data == []
    assert route.call_count == 3


# ----------------------------------------------------------- construction guards


def test_sync_constructs_retry_transport_when_retries_gt_0():
    backend = Backend(Config(retries=3))
    assert isinstance(backend._client._transport, RetryTransport)


def test_sync_no_retry_transport_when_retries_zero():
    backend = Backend(Config(retries=0))
    assert not isinstance(backend._client._transport, RetryTransport)


def test_sync_default_retries_is_three():
    # El valor por defecto de Config debe ser 3 (política recomendada).
    assert Config().retries == 3


def test_sync_injected_client_is_not_wrapped():
    """DI: si el usuario inyecta su httpx.Client, el Backend NO añade RetryTransport."""
    injected = httpx.Client(base_url="https://servicios.ine.es")
    try:
        backend = Backend(Config(retries=3), httpx_client=injected)
        assert backend._client is injected
        # El transporte del cliente inyectado queda intacto (no es RetryTransport
        # salvo que el usuario lo haya puesto él).
        assert not isinstance(injected._transport, RetryTransport)
    finally:
        injected.close()


@pytest.mark.anyio
async def test_async_constructs_retry_transport_when_retries_gt_0():
    backend = AsyncBackend(Config(retries=3))
    try:
        assert isinstance(backend._client._transport, RetryTransport)
    finally:
        await backend.aclose()


@pytest.mark.anyio
async def test_async_injected_client_is_not_wrapped():
    injected = httpx.AsyncClient(base_url="https://servicios.ine.es")
    try:
        backend = AsyncBackend(Config(retries=3), httpx_client=injected)
        assert backend._client is injected
        assert not isinstance(injected._transport, RetryTransport)
    finally:
        await injected.aclose()
