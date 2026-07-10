# tests/test_valores.py
"""Tests del dominio VALORES.

3 endpoints síncronos + 1 asíncrono. Cubre: path correcto (incl.
``VALORES_VARIABLEOPERACION/{id}/{op}`` y ``VALORES_HIJOS/{id}/{id_valor}``),
modelos ``Valor`` reutilizados de series, ``raw=True`` y *param forwarding*
(``det`` / ``clasif``).
"""

import httpx
import pytest
import respx

from ine.async_client import AsyncClient
from ine.client import Client
from ine.models.series import Valor

BASE = "https://servicios.ine.es"
JS = f"{BASE}/wstempus/js/ES"

_VALORES = [
    {"Id": 28, "Nombre": "Total Nacional", "Codigo": "NAC"},
    {"Id": 351, "Nombre": "Andalucía", "Codigo": "04"},
]
_VAL_HIJOS = [
    {"Id": 7405, "Nombre": "Almería", "Codigo": "04"},
    {"Id": 7406, "Nombre": "Cádiz", "Codigo": "11"},
]


def _client() -> Client:
    return Client(retries=0)


# ================================================================ by_variable
@respx.mock
def test_valores_by_variable_path_and_model():
    route = respx.get(f"{JS}/VALORES_VARIABLE/74").mock(
        return_value=httpx.Response(200, json=_VALORES)
    )
    valores = _client().valores.by_variable(74)
    assert route.called
    assert isinstance(valores[0], Valor)
    assert valores[0].id == 28
    assert valores[0].nombre == "Total Nacional"
    assert valores[0].codigo == "NAC"


@respx.mock
def test_valores_by_variable_raw():
    respx.get(f"{JS}/VALORES_VARIABLE/74").mock(return_value=httpx.Response(200, json=_VALORES))
    data = _client().valores.by_variable(74, raw=True)
    assert data == _VALORES


@respx.mock
def test_valores_by_variable_forwards_det_clasif():
    route = respx.get(f"{JS}/VALORES_VARIABLE/74").mock(
        return_value=httpx.Response(200, json=_VALORES)
    )
    _client().valores.by_variable(74, det="1", clasif="2")
    params = route.calls.last.request.url.params
    assert params["det"] == "1"
    assert params["clasif"] == "2"


# ================================================================ by_variable_operacion
@respx.mock
def test_valores_by_variable_operacion_path_and_model():
    route = respx.get(f"{JS}/VALORES_VARIABLEOPERACION/74/IPC").mock(
        return_value=httpx.Response(200, json=_VALORES)
    )
    valores = _client().valores.by_variable_operacion(74, "IPC")
    assert route.called
    assert isinstance(valores[0], Valor)
    assert valores[1].nombre == "Andalucía"


@respx.mock
def test_valores_by_variable_operacion_raw():
    respx.get(f"{JS}/VALORES_VARIABLEOPERACION/74/IPC").mock(
        return_value=httpx.Response(200, json=_VALORES)
    )
    data = _client().valores.by_variable_operacion(74, "IPC", raw=True)
    assert data == _VALORES


# ================================================================ hijos
@respx.mock
def test_valores_hijos_path_and_model():
    route = respx.get(f"{JS}/VALORES_HIJOS/74/28").mock(
        return_value=httpx.Response(200, json=_VAL_HIJOS)
    )
    hijos = _client().valores.hijos(74, 28)
    assert route.called
    assert isinstance(hijos[0], Valor)
    assert hijos[0].id == 7405
    assert hijos[0].nombre == "Almería"


@respx.mock
def test_valores_hijos_raw():
    respx.get(f"{JS}/VALORES_HIJOS/74/28").mock(return_value=httpx.Response(200, json=_VAL_HIJOS))
    data = _client().valores.hijos(74, 28, raw=True)
    assert data == _VAL_HIJOS


# ================================================================ async
@respx.mock
@pytest.mark.anyio
async def test_async_valores_by_variable():
    respx.get(f"{JS}/VALORES_VARIABLE/74").mock(return_value=httpx.Response(200, json=_VALORES))
    async with AsyncClient(retries=0) as c:
        valores = await c.valores.by_variable(74)
    assert isinstance(valores[0], Valor)
    assert valores[0].codigo == "NAC"


@respx.mock
@pytest.mark.anyio
async def test_async_valores_by_variable_operacion():
    respx.get(f"{JS}/VALORES_VARIABLEOPERACION/74/IPC").mock(
        return_value=httpx.Response(200, json=_VALORES)
    )
    async with AsyncClient(retries=0) as c:
        valores = await c.valores.by_variable_operacion(74, "IPC")
    assert isinstance(valores[0], Valor)


@respx.mock
@pytest.mark.anyio
async def test_async_valores_hijos():
    respx.get(f"{JS}/VALORES_HIJOS/74/28").mock(return_value=httpx.Response(200, json=_VAL_HIJOS))
    async with AsyncClient(retries=0) as c:
        hijos = await c.valores.hijos(74, 28)
    assert isinstance(hijos[0], Valor)
    assert hijos[1].nombre == "Cádiz"
