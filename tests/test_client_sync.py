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
        return_value=httpx.Response(200, json=[{"Id": 4, "Nombre": "Op"}])
    )
    from ine.models.operaciones import Operacion

    ops = make_client().operaciones.list()
    assert isinstance(ops[0], Operacion)
    assert ops[0].id == 4


@respx.mock
def test_get_tablas_passes_operacion_in_path():
    route = respx.get("https://servicios.ine.es/wstempus/js/ES/TABLAS_OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[{"Id": 1, "Nombre": "T"}])
    )
    Client().tablas.by_operacion("IPC")
    assert route.called


@respx.mock
def test_get_datos_tabla_hits_path_with_id():
    # El id va en el path; el reenvío de query params se cubre en test_namespaces_params.py
    route = respx.get("https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/24077").mock(
        return_value=httpx.Response(200, json=[{"Data": []}])
    )
    Client().datos.tabla("24077", raw=True)
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
    Client(lang=Lang.EN).operaciones.list()
    assert route.called


@respx.mock
def test_client_propagates_logical_error():
    respx.get("https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json="La operación indicada no existe (X)")
    )
    with pytest.raises(INELogicalError):
        Client().operaciones.list()
