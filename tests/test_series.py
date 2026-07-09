# tests/test_series.py
"""Tests del dominio SERIES (Fase 5): 5 endpoints sync + 1 async + modelos.

Cobertura:
- Path correcto y reenvío de params (det/tip escalares, ``page`` int, ``tv``
  lista como query repetida, ``g1``/``g2`` de filtros).
- Modo modelo vs ``raw=True`` (dicts).
- Mapeo ``COD``->``cod`` y ``Operacion`` anidado->``operacion``.
- ``extra='ignore'`` descarta Periodicidad/Escala/Unidad/Clasificacion/T3_*.
"""

import httpx
import pytest
import respx

from ine.async_client import AsyncClient
from ine.client import Client
from ine.models.series import Serie, Valor

BASE = "https://servicios.ine.es"

# SeriesJSON realista: COD (no Codigo), FK_Operacion, Operacion anidada, y
# campos anidados/stray que deben descartarse vía extra='ignore'.
SERIE_JSON = {
    "Id": 230202,
    "COD": "CP0222024",
    "Nombre": "IPC Variación anual. General. Nacional",
    "Decimales": 1,
    "FK_Operacion": 25,
    "Operacion": {"Id": 25, "Cod_IOE": "30453", "Nombre": "IPC", "Codigo": "IPC"},
    "FK_Periodicidad": 1,
    "FK_Publicacion": 1,
    "FK_Clasificacion": 14,
    "FK_Escala": 1,
    "FK_Unidad": 8,
    # Stray (dominio MAESTROS / T3) — se descartan:
    "Periodicidad": {"Id": 1, "Nombre": "Mensual"},
    "Escala": {"Id": 1, "Nombre": "Índice"},
    "Unidad": {"Id": 8, "Nombre": "Variación anual"},
    "Clasificacion": {"Id": 14, "Nombre": "CNAE-2009"},
    "T3_Operacion": "ipc",
}

VALOR_JSON = {
    "Id": 84,
    "Nombre": "Total",
    "Codigo": "T",
    "FK_Variable": 3,
    "T3_Variable": "sector",
}


# ====================================================================== MODELS
def test_serie_model_maps_cod_and_nested_operacion():
    s = Serie.model_validate(SERIE_JSON)
    assert s.id == 230202
    assert s.cod == "CP0222024"
    assert s.nombre.startswith("IPC")
    assert s.decimales == 1
    assert s.fk_operacion == 25
    # Operacion anidada se valida como modelo Operacion
    assert s.operacion is not None
    assert s.operacion.id == 25
    assert s.operacion.codigo == "IPC"
    assert s.fk_periodicidad == 1
    assert s.fk_unidad == 8
    # Los stray (Periodicidad/Escala/Unidad/Clasificacion/T3_*) NO son campos:
    assert not hasattr(s, "periodicidad")
    assert not hasattr(s, "t3_operacion")


def test_serie_model_minimal():
    s = Serie.model_validate({"COD": "X1", "Nombre": "N", "Decimales": 2})
    assert s.cod == "X1"
    assert s.decimales == 2
    assert s.operacion is None
    assert s.fk_operacion is None


def test_valor_model_maps_fields():
    v = Valor.model_validate(VALOR_JSON)
    assert v.id == 84
    assert v.nombre == "Total"
    assert v.codigo == "T"
    assert v.fk_variable == 3
    assert v.t3_variable == "sector"


def test_valor_model_extra_ignored():
    v = Valor.model_validate({"Nombre": "N", "Variable": {"Id": 3}, "FooBar": 1})
    assert v.nombre == "N"
    assert not hasattr(v, "variable")
    assert not hasattr(v, "foo_bar")


# ================================================================= get_serie
@respx.mock
def test_get_serie_hits_path_and_maps():
    route = respx.get(f"{BASE}/wstempus/js/ES/SERIE/CP0222024").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    series = Client().series.get("CP0222024")
    assert route.called
    assert isinstance(series[0], Serie)
    assert series[0].cod == "CP0222024"
    assert series[0].operacion is not None
    assert series[0].operacion.codigo == "IPC"


@respx.mock
def test_get_serie_forwards_det_tip():
    route = respx.get(f"{BASE}/wstempus/js/ES/SERIE/CP0222024").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    Client().series.get("CP0222024", det="2", tip="AM")
    params = route.calls.last.request.url.params
    assert params["det"] == "2"
    assert params["tip"] == "AM"


@respx.mock
def test_get_serie_no_query_when_none():
    route = respx.get(f"{BASE}/wstempus/js/ES/SERIE/CP0222024").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    Client().series.get("CP0222024")
    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
def test_get_serie_raw():
    respx.get(f"{BASE}/wstempus/js/ES/SERIE/CP0222024").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    data = Client().series.get("CP0222024", raw=True)
    assert data == [SERIE_JSON]


# =========================================================== get_series_operacion
@respx.mock
def test_get_series_operacion_hits_path():
    route = respx.get(f"{BASE}/wstempus/js/ES/SERIES_OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    series = Client().series.by_operacion("IPC")
    assert route.called
    assert isinstance(series[0], Serie)


@respx.mock
def test_get_series_operacion_forwards_page_int():
    route = respx.get(f"{BASE}/wstempus/js/ES/SERIES_OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    Client().series.by_operacion("IPC", page=2, det="1")
    params = route.calls.last.request.url.params
    assert params["page"] == "2"
    assert params["det"] == "1"


@respx.mock
def test_get_series_operacion_raw():
    respx.get(f"{BASE}/wstempus/js/ES/SERIES_OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    data = Client().series.by_operacion("IPC", raw=True)
    assert data == [SERIE_JSON]


# =============================================================== get_series_tabla
@respx.mock
def test_get_series_tabla_hits_path():
    route = respx.get(f"{BASE}/wstempus/js/ES/SERIES_TABLA/24077").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    series = Client().series.by_tabla("24077")
    assert route.called
    assert isinstance(series[0], Serie)


@respx.mock
def test_get_series_tabla_forwards_tv_as_repeated_query():
    route = respx.get(f"{BASE}/wstempus/js/ES/SERIES_TABLA/24077").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    Client().series.by_tabla("24077", tv=["1:2", "3:84"])
    assert route.calls.last.request.url.params.get_list("tv") == ["1:2", "3:84"]


@respx.mock
def test_get_series_tabla_raw():
    respx.get(f"{BASE}/wstempus/js/ES/SERIES_TABLA/24077").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    data = Client().series.by_tabla("24077", raw=True)
    assert data == [SERIE_JSON]


# ============================================================= get_valores_serie
@respx.mock
def test_get_valores_serie_hits_path_and_maps():
    route = respx.get(f"{BASE}/wstempus/js/ES/VALORES_SERIE/CP0222024").mock(
        return_value=httpx.Response(200, json=[VALOR_JSON])
    )
    valores = Client().series.valores("CP0222024")
    assert route.called
    assert isinstance(valores[0], Valor)
    assert valores[0].codigo == "T"
    assert valores[0].fk_variable == 3


@respx.mock
def test_get_valores_serie_forwards_det():
    route = respx.get(f"{BASE}/wstempus/js/ES/VALORES_SERIE/CP0222024").mock(
        return_value=httpx.Response(200, json=[VALOR_JSON])
    )
    Client().series.valores("CP0222024", det="1")
    assert route.calls.last.request.url.params["det"] == "1"


@respx.mock
def test_get_valores_serie_raw():
    respx.get(f"{BASE}/wstempus/js/ES/VALORES_SERIE/CP0222024").mock(
        return_value=httpx.Response(200, json=[VALOR_JSON])
    )
    data = Client().series.valores("CP0222024", raw=True)
    assert data == [VALOR_JSON]


# ================================================= get_series_metadata_operacion
@respx.mock
def test_get_series_metadata_operacion_hits_path():
    route = respx.get(f"{BASE}/wstempus/js/ES/SERIE_METADATAOPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    series = Client().series.metadata_operacion("IPC")
    assert route.called
    assert isinstance(series[0], Serie)


@respx.mock
def test_get_series_metadata_operacion_compiles_filtros_to_g():
    route = respx.get(f"{BASE}/wstempus/js/ES/SERIE_METADATAOPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    Client().series.metadata_operacion(
        "IPC", p="12", filtros=[("115", ["29", "30"]), ("3", ["84"])]
    )
    params = route.calls.last.request.url.params
    assert params["p"] == "12"
    assert params.get_list("g1") == ["115:29", "115:30"]
    assert params["g2"] == "3:84"


@respx.mock
def test_get_series_metadata_operacion_no_filtros_means_no_g():
    route = respx.get(f"{BASE}/wstempus/js/ES/SERIE_METADATAOPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    Client().series.metadata_operacion("IPC")
    params = dict(route.calls.last.request.url.params)
    assert not any(k.startswith("g") for k in params)


@respx.mock
def test_get_series_metadata_operacion_raw():
    respx.get(f"{BASE}/wstempus/js/ES/SERIE_METADATAOPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    data = Client().series.metadata_operacion("IPC", raw=True)
    assert data == [SERIE_JSON]


# ================================================================ ASYNC CLIENT
@respx.mock
@pytest.mark.anyio
async def test_async_get_serie_maps_cod_and_operacion():
    respx.get(f"{BASE}/wstempus/js/ES/SERIE/CP0222024").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    async with AsyncClient() as c:
        series = await c.series.get("CP0222024")
    assert isinstance(series[0], Serie)
    assert series[0].cod == "CP0222024"
    assert series[0].operacion is not None
    assert series[0].operacion.codigo == "IPC"


@respx.mock
@pytest.mark.anyio
async def test_async_get_series_tabla_forwards_tv_repeated():
    route = respx.get(f"{BASE}/wstempus/js/ES/SERIES_TABLA/24077").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    async with AsyncClient() as c:
        await c.series.by_tabla("24077", tv=["1:2", "3:84"])
    assert route.calls.last.request.url.params.get_list("tv") == ["1:2", "3:84"]


@respx.mock
@pytest.mark.anyio
async def test_async_get_series_metadata_operacion_compiles_filtros():
    route = respx.get(f"{BASE}/wstempus/js/ES/SERIE_METADATAOPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[SERIE_JSON])
    )
    async with AsyncClient() as c:
        await c.series.metadata_operacion("IPC", filtros=[("115", ["29", "30"]), ("3", ["84"])])
    params = route.calls.last.request.url.params
    assert params.get_list("g1") == ["115:29", "115:30"]
    assert params["g2"] == "3:84"


@respx.mock
@pytest.mark.anyio
async def test_async_get_valores_serie_raw():
    respx.get(f"{BASE}/wstempus/js/ES/VALORES_SERIE/CP0222024").mock(
        return_value=httpx.Response(200, json=[VALOR_JSON])
    )
    async with AsyncClient() as c:
        data = await c.series.valores("CP0222024", raw=True)
    assert data == [VALOR_JSON]
