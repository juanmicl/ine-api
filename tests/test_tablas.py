# tests/test_tablas.py
"""Tests del dominio TABLAS (extensión).

Cubre los 3 endpoints del namespace ``client.tablas``:

* ``by_operacion`` — upgrade: ahora devuelve ``list[Tabla]`` (antes ``list[dict]``).
  Verifica modelo con ``Periodicidad`` anidada y epoch→datetime de
  ``ultima_modificacion``.
* ``grupos`` — ``GRUPOS_TABLA/{id_tabla}`` → ``list[Grupo]``.
* ``valores_grupo`` — ``VALORES_GRUPOSTABLA/{id_tabla}/{id_grupo}`` → ``list[Valor]``.
"""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from ine.async_client import AsyncClient
from ine.client import Client
from ine.models.maestros import Periodicidad
from ine.models.series import Valor
from ine.models.tablas import Grupo, Tabla

BASE = "https://servicios.ine.es"
JS = f"{BASE}/wstempus/js/ES"

_TABLAS = [
    {
        "Id": 24077,
        "Nombre": "Índice general nacional",
        "Codigo": "NAC",
        "FK_Periodicidad": 1,
        "Periodicidad": [{"Id": 1, "Nombre": "Mensual", "Codigo": "M"}],
        "FK_Publicacion": 8,
        "UltimaModificacion": 1293840000000,
    }
]
_GRUPOS = [
    {"Id": 1, "Nombre": "General"},
    {"Id": 2, "Nombre": "Grupos de gasto"},
]
_VAL_GRUPO = [
    {"Id": 1, "Nombre": "Índice general", "Codigo": "01"},
    {"Id": 2, "Nombre": "Alimentos", "Codigo": "11"},
]
_EPOCH = datetime.fromtimestamp(1293840000000 / 1000, tz=UTC)


def _client() -> Client:
    return Client(retries=0)


# ================================================================ by_operacion (upgrade)
@respx.mock
def test_by_operacion_returns_tabla_models():
    route = respx.get(f"{JS}/TABLAS_OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=_TABLAS)
    )
    tablas = _client().tablas.by_operacion("IPC")
    assert route.called
    assert isinstance(tablas[0], Tabla)
    assert tablas[0].id == 24077
    assert tablas[0].nombre == "Índice general nacional"
    assert tablas[0].codigo == "NAC"
    assert tablas[0].fk_periodicidad == 1
    assert tablas[0].fk_publicacion == 8


@respx.mock
def test_by_operacion_nested_periodicidad():
    respx.get(f"{JS}/TABLAS_OPERACION/IPC").mock(return_value=httpx.Response(200, json=_TABLAS))
    tablas = _client().tablas.by_operacion("IPC")
    assert isinstance(tablas[0].periodicidad[0], Periodicidad)
    assert tablas[0].periodicidad[0].codigo == "M"


@respx.mock
def test_by_operacion_epoch_to_datetime():
    respx.get(f"{JS}/TABLAS_OPERACION/IPC").mock(return_value=httpx.Response(200, json=_TABLAS))
    tablas = _client().tablas.by_operacion("IPC")
    assert tablas[0].ultima_modificacion == _EPOCH


@respx.mock
def test_by_operacion_raw_still_returns_dict():
    respx.get(f"{JS}/TABLAS_OPERACION/IPC").mock(return_value=httpx.Response(200, json=_TABLAS))
    data = _client().tablas.by_operacion("IPC", raw=True)
    assert data == _TABLAS


# ================================================================ grupos
@respx.mock
def test_grupos_path_and_model():
    route = respx.get(f"{JS}/GRUPOS_TABLA/24077").mock(
        return_value=httpx.Response(200, json=_GRUPOS)
    )
    grupos = _client().tablas.grupos("24077")
    assert route.called
    assert isinstance(grupos[0], Grupo)
    assert grupos[0].id == 1
    assert grupos[0].nombre == "General"
    assert grupos[1].nombre == "Grupos de gasto"


@respx.mock
def test_grupos_raw():
    respx.get(f"{JS}/GRUPOS_TABLA/24077").mock(return_value=httpx.Response(200, json=_GRUPOS))
    data = _client().tablas.grupos("24077", raw=True)
    assert data == _GRUPOS


# ================================================================ valores_grupo
@respx.mock
def test_valores_grupo_path_and_model():
    route = respx.get(f"{JS}/VALORES_GRUPOSTABLA/24077/1").mock(
        return_value=httpx.Response(200, json=_VAL_GRUPO)
    )
    valores = _client().tablas.valores_grupo("24077", 1)
    assert route.called
    assert isinstance(valores[0], Valor)
    assert valores[0].id == 1
    assert valores[0].nombre == "Índice general"
    assert valores[0].codigo == "01"


@respx.mock
def test_valores_grupo_raw():
    respx.get(f"{JS}/VALORES_GRUPOSTABLA/24077/1").mock(
        return_value=httpx.Response(200, json=_VAL_GRUPO)
    )
    data = _client().tablas.valores_grupo("24077", 1, raw=True)
    assert data == _VAL_GRUPO


@respx.mock
def test_valores_grupo_forwards_det():
    route = respx.get(f"{JS}/VALORES_GRUPOSTABLA/24077/1").mock(
        return_value=httpx.Response(200, json=_VAL_GRUPO)
    )
    _client().tablas.valores_grupo("24077", 1, det="1")
    params = route.calls.last.request.url.params
    assert params["det"] == "1"


# ================================================================ async
@respx.mock
@pytest.mark.anyio
async def test_async_by_operacion_returns_tabla():
    respx.get(f"{JS}/TABLAS_OPERACION/IPC").mock(return_value=httpx.Response(200, json=_TABLAS))
    async with AsyncClient(retries=0) as c:
        tablas = await c.tablas.by_operacion("IPC")
    assert isinstance(tablas[0], Tabla)
    assert tablas[0].ultima_modificacion == _EPOCH


@respx.mock
@pytest.mark.anyio
async def test_async_grupos():
    respx.get(f"{JS}/GRUPOS_TABLA/24077").mock(return_value=httpx.Response(200, json=_GRUPOS))
    async with AsyncClient(retries=0) as c:
        grupos = await c.tablas.grupos("24077")
    assert isinstance(grupos[0], Grupo)


@respx.mock
@pytest.mark.anyio
async def test_async_valores_grupo():
    respx.get(f"{JS}/VALORES_GRUPOSTABLA/24077/1").mock(
        return_value=httpx.Response(200, json=_VAL_GRUPO)
    )
    async with AsyncClient(retries=0) as c:
        valores = await c.tablas.valores_grupo("24077", 1)
    assert isinstance(valores[0], Valor)
    assert valores[1].nombre == "Alimentos"
