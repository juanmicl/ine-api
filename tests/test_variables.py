# tests/test_variables.py
"""Tests del dominio VARIABLES.

3 endpoints síncronos + 2 asíncronos. Cubre: path correcto, ``page`` en query,
``variable(id)`` via ``get_one`` (single → Variable, NO lista), ``raw=True`` y
op en path.
"""

import httpx
import pytest
import respx

from ine.async_client import AsyncClient
from ine.client import Client
from ine.models.variables import Variable

BASE = "https://servicios.ine.es"
JS = f"{BASE}/wstempus/js/ES"

_VAR_LIST = [{"Id": 349, "Nombre": "Total Nacional", "Codigo": "NAC"}]
_VAR_ONE = {"Id": 349, "Nombre": "Total Nacional", "Codigo": "NAC"}


def _client() -> Client:
    return Client(retries=0)


# ================================================================ variables
@respx.mock
def test_variables_returns_list_of_models():
    route = respx.get(f"{JS}/VARIABLES").mock(return_value=httpx.Response(200, json=_VAR_LIST))
    variables = _client().variables.variables()
    assert route.called
    assert isinstance(variables[0], Variable)
    assert variables[0].id == 349
    assert variables[0].nombre == "Total Nacional"
    assert variables[0].codigo == "NAC"


@respx.mock
def test_variables_page_in_query():
    route = respx.get(f"{JS}/VARIABLES").mock(return_value=httpx.Response(200, json=_VAR_LIST))
    _client().variables.variables(page=2)
    assert route.calls.last.request.url.params["page"] == "2"


@respx.mock
def test_variables_raw():
    respx.get(f"{JS}/VARIABLES").mock(return_value=httpx.Response(200, json=_VAR_LIST))
    data = _client().variables.variables(raw=True)
    assert data == _VAR_LIST


@respx.mock
def test_variables_operacion_has_op_in_path():
    route = respx.get(f"{JS}/VARIABLES_OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=_VAR_LIST)
    )
    variables = _client().variables.variables_operacion("IPC")
    assert route.called
    assert isinstance(variables[0], Variable)


# ================================================================ variable (single)
@respx.mock
def test_variable_returns_single_model():
    route = respx.get(f"{JS}/VARIABLE/349").mock(return_value=httpx.Response(200, json=_VAR_ONE))
    variable = _client().variables.variable(349)
    assert route.called
    assert isinstance(variable, Variable)  # NO es una lista
    assert variable.id == 349
    assert variable.codigo == "NAC"


@respx.mock
def test_variable_raw():
    respx.get(f"{JS}/VARIABLE/349").mock(return_value=httpx.Response(200, json=_VAR_ONE))
    data = _client().variables.variable(349, raw=True)
    assert data == _VAR_ONE


# ================================================================ async
@respx.mock
@pytest.mark.anyio
async def test_async_variables():
    respx.get(f"{JS}/VARIABLES").mock(return_value=httpx.Response(200, json=_VAR_LIST))
    async with AsyncClient(retries=0) as c:
        variables = await c.variables.variables()
    assert isinstance(variables[0], Variable)
    assert variables[0].codigo == "NAC"


@respx.mock
@pytest.mark.anyio
async def test_async_variable():
    respx.get(f"{JS}/VARIABLE/349").mock(return_value=httpx.Response(200, json=_VAR_ONE))
    async with AsyncClient(retries=0) as c:
        variable = await c.variables.variable(349)
    assert isinstance(variable, Variable)
    assert variable.nombre == "Total Nacional"
