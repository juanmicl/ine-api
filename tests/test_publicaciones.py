# tests/test_publicaciones.py
"""Tests del dominio PUBLICACIONES.

3 endpoints síncronos + 1 asíncrono. Cubre: path correcto (incl.
``PUBLICACIONFECHA_PUBLICACION/{id}``), modelos con ``Periodicidad`` anidada,
epoch→datetime de ``PublicacionFecha.fecha``, ``raw=True`` y op en path.
"""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from ine.async_client import AsyncClient
from ine.client import Client
from ine.models.maestros import Periodicidad
from ine.models.publicaciones import Publicacion, PublicacionFecha

BASE = "https://servicios.ine.es"
JS = f"{BASE}/wstempus/js/ES"

_PUB_LIST = [
    {
        "Id": 1,
        "Nombre": "Coyuntura Turística",
        "FK_Periodicidad": 1,
        "Periodicidad": [{"Id": 1, "Nombre": "Mensual", "Codigo": "M"}],
        "FK_PubFechaAct": 12597,
    }
]
_PUB_FECHA_LIST = [
    {
        "Id": 8765,
        "Nombre": "Enero 2011",
        "Fecha": 1293840000000,
        "Anyo": 2011,
        "FK_Publicacion": 8,
        "FK_Periodo": 1,
    }
]
_EPOCH = datetime.fromtimestamp(1293840000000 / 1000, tz=UTC)


def _client() -> Client:
    return Client(retries=0)


# ================================================================ publicaciones
@respx.mock
def test_publicaciones_returns_list_with_nested_periodicidad():
    route = respx.get(f"{JS}/PUBLICACIONES").mock(return_value=httpx.Response(200, json=_PUB_LIST))
    pubs = _client().publicaciones.publicaciones()
    assert route.called
    assert isinstance(pubs[0], Publicacion)
    assert pubs[0].id == 1
    assert pubs[0].nombre == "Coyuntura Turística"
    assert pubs[0].fk_periodicidad == 1
    assert pubs[0].fk_pub_fecha_act == 12597
    # Periodicidad anidada → list[Periodicidad]
    assert isinstance(pubs[0].periodicidad[0], Periodicidad)
    assert pubs[0].periodicidad[0].codigo == "M"


@respx.mock
def test_publicaciones_raw():
    respx.get(f"{JS}/PUBLICACIONES").mock(return_value=httpx.Response(200, json=_PUB_LIST))
    data = _client().publicaciones.publicaciones(raw=True)
    assert data == _PUB_LIST


@respx.mock
def test_publicaciones_operacion_has_op_in_path():
    route = respx.get(f"{JS}/PUBLICACIONES_OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=_PUB_LIST)
    )
    pubs = _client().publicaciones.publicaciones_operacion("IPC")
    assert route.called
    assert isinstance(pubs[0], Publicacion)


# ================================================================ publicacion_fecha
@respx.mock
def test_publicacion_fecha_parses_epoch_and_path():
    route = respx.get(f"{JS}/PUBLICACIONFECHA_PUBLICACION/8").mock(
        return_value=httpx.Response(200, json=_PUB_FECHA_LIST)
    )
    fechas = _client().publicaciones.publicacion_fecha(8)
    assert route.called
    assert isinstance(fechas[0], PublicacionFecha)
    assert fechas[0].id == 8765
    assert fechas[0].anyo == 2011
    assert fechas[0].fk_publicacion == 8
    assert fechas[0].fk_periodo == 1
    assert fechas[0].fecha == _EPOCH


@respx.mock
def test_publicacion_fecha_raw():
    respx.get(f"{JS}/PUBLICACIONFECHA_PUBLICACION/8").mock(
        return_value=httpx.Response(200, json=_PUB_FECHA_LIST)
    )
    data = _client().publicaciones.publicacion_fecha(8, raw=True)
    assert data == _PUB_FECHA_LIST


# ================================================================ async
@respx.mock
@pytest.mark.anyio
async def test_async_publicaciones():
    respx.get(f"{JS}/PUBLICACIONES").mock(return_value=httpx.Response(200, json=_PUB_LIST))
    async with AsyncClient(retries=0) as c:
        pubs = await c.publicaciones.publicaciones()
    assert isinstance(pubs[0], Publicacion)
    assert pubs[0].periodicidad[0].codigo == "M"


@respx.mock
@pytest.mark.anyio
async def test_async_publicacion_fecha():
    respx.get(f"{JS}/PUBLICACIONFECHA_PUBLICACION/8").mock(
        return_value=httpx.Response(200, json=_PUB_FECHA_LIST)
    )
    async with AsyncClient(retries=0) as c:
        fechas = await c.publicaciones.publicacion_fecha(8)
    assert isinstance(fechas[0], PublicacionFecha)
    assert fechas[0].fecha == _EPOCH
