# tests/test_client_sync.py
import httpx
import pytest
import respx

from ine._config import Lang
from ine.client import Client
from ine.errors import INELogicalError


def make_client():
    return Client(lang=Lang.ES)


@respx.mock
def test_get_operaciones():
    respx.get("https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=[{"Id": 4}])
    )
    assert make_client().get_operaciones() == [{"Id": 4}]


@respx.mock
def test_get_tablas_passes_operacion_in_path():
    route = respx.get("https://servicios.ine.es/wstempus/js/ES/TABLAS_OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[{"Id": 1}])
    )
    Client().get_tablas("IPC")
    assert route.called


@respx.mock
def test_get_datos_tabla_passes_params():
    # compat: firma actual sin params extra, pero el path debe contener el id
    route = respx.get("https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/24077").mock(
        return_value=httpx.Response(200, json=[{"Data": []}])
    )
    Client().get_datos_tabla("24077")
    assert route.called


def test_client_is_context_manager():
    with Client() as c:
        assert isinstance(c, Client)
    # debe poder cerrarse sin error


def test_client_uses_injected_httpx_client():
    injected = httpx.Client(base_url="https://servicios.ine.es")
    c = Client(httpx_client=injected)
    assert c._backend._client is injected  # no creó uno nuevo


@respx.mock
def test_client_lang_en_in_path():
    route = respx.get("https://servicios.ine.es/wstempus/js/EN/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=[])
    )
    Client(lang=Lang.EN).get_operaciones()
    assert route.called


@respx.mock
def test_client_propagates_logical_error():
    respx.get("https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json="La operación indicada no existe (X)")
    )
    with pytest.raises(INELogicalError):
        Client().get_operaciones()
