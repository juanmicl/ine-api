# tests/test_maestros.py
"""Tests del dominio MAESTROS (escalas, unidades, periodos, periodicidades,
clasificaciones).

10 endpoints síncronos + 2 asíncronos. Cubre: path correcto, modelos de retorno,
``raw=True`` (fidelidad del JSON crudo) y el parseo epoch→datetime de
``Clasificacion.fecha``. Los endpoints individuales (escala/unidad/periodo/
periodicidad) usan ``get_one`` → devuelven un modelo directo (no una lista).
"""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from ine.async_client import AsyncClient
from ine.client import Client
from ine.models.maestros import (
    Clasificacion,
    Escala,
    Periodicidad,
    Periodo,
    Unidad,
)

BASE = "https://servicios.ine.es"
JS = f"{BASE}/wstempus/js/ES"

# --- payloads reales (capturados de la API del INE) ---

_ESCALA_LIST = [{"Id": 1, "Nombre": " ", "Factor": "1E0", "Codigo": "0", "Abrev": None}]
_ESCALA_ONE = {"Id": 1, "Nombre": "Decenas", "Factor": "1E1", "Codigo": "1", "Abrev": "Decenas"}
_UNIDAD_LIST = [{"Id": 3, "Nombre": "Personas", "Codigo": None, "Abrev": None}]
_UNIDAD_ONE = {"Id": 3, "Nombre": "Personas", "Codigo": None, "Abrev": None}
_PERIODO_ONE = {
    "Id": 13,
    "Valor": 1,
    "FK_Periodicidad": 1,
    "Dia_Inicio": "01",
    "Mes_Inicio": "01",
    "Codigo": "M01",
    "Nombre": "Enero",
    "Nombre_Largo": "Enero 2020",
}
_PERIODICIDAD_LIST = [{"Id": 1, "Nombre": "Mensual", "Codigo": "M"}]
_PERIODICIDAD_ONE = {"Id": 1, "Nombre": "Mensual", "Codigo": "M"}
_CLASIF_LIST = [{"Id": 1, "Nombre": "CNAE 93", "Fecha": 725842800000}]
_EPOCH = datetime.fromtimestamp(725842800000 / 1000, tz=UTC)


def _client() -> Client:
    return Client(retries=0)


# ================================================================ Escalas
@respx.mock
def test_escalas_returns_list_of_models():
    route = respx.get(f"{JS}/ESCALAS").mock(return_value=httpx.Response(200, json=_ESCALA_LIST))
    escalas = _client().maestros.escalas()
    assert route.called
    assert isinstance(escalas[0], Escala)
    assert escalas[0].id == 1
    assert escalas[0].factor == "1E0"
    assert escalas[0].codigo == "0"


@respx.mock
def test_escalas_raw():
    respx.get(f"{JS}/ESCALAS").mock(return_value=httpx.Response(200, json=_ESCALA_LIST))
    data = _client().maestros.escalas(raw=True)
    assert data == _ESCALA_LIST


@respx.mock
def test_escala_returns_single_model():
    route = respx.get(f"{JS}/ESCALA/1").mock(return_value=httpx.Response(200, json=_ESCALA_ONE))
    escala = _client().maestros.escala(1)
    assert route.called
    assert isinstance(escala, Escala)  # NO es una lista
    assert escala.id == 1
    assert escala.nombre == "Decenas"
    assert escala.factor == "1E1"


@respx.mock
def test_escala_raw():
    respx.get(f"{JS}/ESCALA/1").mock(return_value=httpx.Response(200, json=_ESCALA_ONE))
    data = _client().maestros.escala(1, raw=True)
    assert data == _ESCALA_ONE


# ================================================================ Unidades
@respx.mock
def test_unidades_returns_list_of_models():
    route = respx.get(f"{JS}/UNIDADES").mock(return_value=httpx.Response(200, json=_UNIDAD_LIST))
    unidades = _client().maestros.unidades()
    assert route.called
    assert isinstance(unidades[0], Unidad)
    assert unidades[0].id == 3
    assert unidades[0].nombre == "Personas"


@respx.mock
def test_unidad_returns_single_model():
    route = respx.get(f"{JS}/UNIDAD/3").mock(return_value=httpx.Response(200, json=_UNIDAD_ONE))
    unidad = _client().maestros.unidad(3)
    assert route.called
    assert isinstance(unidad, Unidad)
    assert unidad.nombre == "Personas"


@respx.mock
def test_unidades_operacion_has_op_in_path():
    route = respx.get(f"{JS}/UNIDADES_OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=_UNIDAD_LIST)
    )
    unidades = _client().maestros.unidades_operacion("IPC")
    assert route.called
    assert isinstance(unidades[0], Unidad)


# ================================================================ Periodos
@respx.mock
def test_periodo_returns_rich_model():
    route = respx.get(f"{JS}/PERIODO/13").mock(return_value=httpx.Response(200, json=_PERIODO_ONE))
    periodo = _client().maestros.periodo(13)
    assert route.called
    assert isinstance(periodo, Periodo)
    assert periodo.id == 13
    assert periodo.valor == 1
    assert periodo.fk_periodicidad == 1
    assert periodo.dia_inicio == "01"
    assert periodo.mes_inicio == "01"
    assert periodo.codigo == "M01"
    assert periodo.nombre == "Enero"
    assert periodo.nombre_largo == "Enero 2020"


@respx.mock
def test_periodo_raw():
    respx.get(f"{JS}/PERIODO/13").mock(return_value=httpx.Response(200, json=_PERIODO_ONE))
    data = _client().maestros.periodo(13, raw=True)
    assert data == _PERIODO_ONE


# ================================================================ Periodicidades
@respx.mock
def test_periodicidades_returns_list_of_models():
    route = respx.get(f"{JS}/PERIODICIDADES").mock(
        return_value=httpx.Response(200, json=_PERIODICIDAD_LIST)
    )
    periodicidades = _client().maestros.periodicidades()
    assert route.called
    assert isinstance(periodicidades[0], Periodicidad)
    assert periodicidades[0].id == 1
    assert periodicidades[0].codigo == "M"


@respx.mock
def test_periodicidad_returns_single_model():
    route = respx.get(f"{JS}/PERIODICIDAD/1").mock(
        return_value=httpx.Response(200, json=_PERIODICIDAD_ONE)
    )
    periodicidad = _client().maestros.periodicidad(1)
    assert route.called
    assert isinstance(periodicidad, Periodicidad)
    assert periodicidad.nombre == "Mensual"


# ================================================================ Clasificaciones
@respx.mock
def test_clasificaciones_parses_epoch_fecha():
    route = respx.get(f"{JS}/CLASIFICACIONES").mock(
        return_value=httpx.Response(200, json=_CLASIF_LIST)
    )
    clasifs = _client().maestros.clasificaciones()
    assert route.called
    assert isinstance(clasifs[0], Clasificacion)
    assert clasifs[0].id == 1
    assert clasifs[0].nombre == "CNAE 93"
    assert clasifs[0].fecha == _EPOCH


@respx.mock
def test_clasificaciones_raw():
    respx.get(f"{JS}/CLASIFICACIONES").mock(return_value=httpx.Response(200, json=_CLASIF_LIST))
    data = _client().maestros.clasificaciones(raw=True)
    assert data == _CLASIF_LIST


@respx.mock
def test_clasificaciones_operacion_has_op_in_path():
    route = respx.get(f"{JS}/CLASIFICACIONES_OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=_CLASIF_LIST)
    )
    clasifs = _client().maestros.clasificaciones_operacion("IPC")
    assert route.called
    assert isinstance(clasifs[0], Clasificacion)
    assert clasifs[0].fecha == _EPOCH


# ================================================================ Async
@respx.mock
@pytest.mark.anyio
async def test_async_escalas():
    respx.get(f"{JS}/ESCALAS").mock(return_value=httpx.Response(200, json=_ESCALA_LIST))
    async with AsyncClient(retries=0) as c:
        escalas = await c.maestros.escalas()
    assert isinstance(escalas[0], Escala)
    assert escalas[0].id == 1


@respx.mock
@pytest.mark.anyio
async def test_async_escala():
    respx.get(f"{JS}/ESCALA/1").mock(return_value=httpx.Response(200, json=_ESCALA_ONE))
    async with AsyncClient(retries=0) as c:
        escala = await c.maestros.escala(1)
    assert isinstance(escala, Escala)
    assert escala.factor == "1E1"
