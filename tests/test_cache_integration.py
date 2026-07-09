# tests/test_cache_integration.py
"""Integración del cache opt-in en Backend/Client (comportamiento vía respx).

Cubre: cache=None siempre hace HTTP; cache=Cache() hit en 2ª llamada; los
``INEError`` no se cachean; distintos params → distintas entradas; expiración
TTL → refetch; sync y async comparten un mismo store; y el reexport público.
"""

import httpx
import pytest
import respx

from ine import Cache
from ine._cache import Cache as _Cache
from ine.async_client import AsyncClient
from ine.client import Client
from ine.errors import INENotFoundError

_OPERACIONES = "https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES"


@respx.mock
def test_cache_none_default_always_hits_http():
    # cache=None (default) => sin cache: dos llamadas = dos peticiones HTTP.
    route = respx.get(_OPERACIONES).mock(
        return_value=httpx.Response(200, json=[{"Id": 4, "Nombre": "Op"}])
    )
    with Client(retries=0) as c:
        c.operaciones.list(raw=True)
        c.operaciones.list(raw=True)
    assert route.call_count == 2


@respx.mock
def test_cache_hit_on_second_call():
    # cache=Cache(): 2ª llamada es hit (1 sola petición HTTP); datos iguales.
    cache = Cache(ttl=300)
    route = respx.get(_OPERACIONES).mock(
        return_value=httpx.Response(200, json=[{"Id": 4, "Nombre": "Op"}])
    )
    with Client(retries=0, cache=cache) as c:
        first = c.operaciones.list(raw=True)
        second = c.operaciones.list(raw=True)
    assert route.call_count == 1
    assert first == second


@respx.mock
def test_errors_are_not_cached():
    # Un INEError (404) se propaga SIN tocar el cache; la siguiente llamada
    # exitosa hace fetch fresco (no devuelve el error stale).
    cache = Cache(ttl=300)
    route = respx.get(_OPERACIONES).mock(
        side_effect=[
            httpx.Response(404, text="no existe"),
            httpx.Response(200, json=[{"Id": 4, "Nombre": "Op"}]),
        ]
    )
    with Client(retries=0, cache=cache) as c:
        with pytest.raises(INENotFoundError):
            c.operaciones.list()
        assert len(cache) == 0  # el error no dejó huella en el cache

        # 2ª llamada: la API ya responde 200 -> fetch fresco y se cachea el éxito.
        c.operaciones.list(raw=True)
    assert route.call_count == 2
    assert len(cache) == 1


@respx.mock
def test_different_params_do_not_collide():
    # Distintos (path, params) => entradas distintas; repetir la 1ª es hit.
    cache = Cache(ttl=300)
    route_111 = respx.get("https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/111").mock(
        return_value=httpx.Response(200, json=[{"Cod": "S111", "Nombre": "S", "Data": []}])
    )
    route_222 = respx.get("https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/222").mock(
        return_value=httpx.Response(200, json=[{"Cod": "S222", "Nombre": "S", "Data": []}])
    )

    with Client(retries=0, cache=cache) as c:
        c.datos.serie("111", nult=1, raw=True)
        c.datos.serie("222", raw=True)
        assert route_111.call_count == 1
        assert route_222.call_count == 1

        # repetir la primera => hit, sin nueva petición HTTP.
        c.datos.serie("111", nult=1, raw=True)
    assert route_111.call_count == 1
    assert route_222.call_count == 1


@respx.mock
def test_ttl_expiry_triggers_refetch(monkeypatch):
    # Avanzar el reloj más allá del ttl => la próxima llamada refresca.
    t = [0.0]
    monkeypatch.setattr("ine._cache._now", lambda: t[0])

    cache = Cache(ttl=10.0)
    route = respx.get(_OPERACIONES).mock(
        return_value=httpx.Response(200, json=[{"Id": 4, "Nombre": "Op"}])
    )
    with Client(retries=0, cache=cache) as c:
        c.operaciones.list(raw=True)
        assert route.call_count == 1

        t[0] = 5.0  # dentro del ttl => hit
        c.operaciones.list(raw=True)
        assert route.call_count == 1

        t[0] = 100.0  # expirado => refetch
        c.operaciones.list(raw=True)
    assert route.call_count == 2


@respx.mock
@pytest.mark.anyio
async def test_sync_and_async_share_one_cache():
    # Una misma instancia de Cache sirve a Client (sync) y AsyncClient (async).
    cache = Cache(ttl=300)
    route = respx.get(_OPERACIONES).mock(
        return_value=httpx.Response(200, json=[{"Id": 4, "Nombre": "Op"}])
    )

    with Client(retries=0, cache=cache) as c:
        c.operaciones.list(raw=True)
    assert route.call_count == 1

    # misma (path, params) => hit desde el store compartido.
    async with AsyncClient(retries=0, cache=cache) as ac:
        await ac.operaciones.list(raw=True)
    assert route.call_count == 1


def test_cache_public_reexport():
    # from ine import Cache funciona y es la misma clase que ine._cache.Cache.
    from ine import __all__

    assert "Cache" in __all__
    assert Cache is _Cache
