# tests/test_operaciones_datos.py
"""Tests de los endpoints OPERACION (por id) y DATOS (serie + metadataoperacion).

Cobran los 3 métodos nuevos de Client (sync): path correcto, reenvío de
params (det, date lista, g1/g2 de filtros), y modo raw vs modelo.
"""

import httpx
import respx

from ine.client import Client
from ine.models.datos import DatosSerie
from ine.models.operaciones import Operacion

BASE = "https://servicios.ine.es"


# ---------------------------------------------------------------- get_operacion
@respx.mock
def test_get_operacion_hits_path_with_id():
    route = respx.get(f"{BASE}/wstempus/js/ES/OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[{"Id": 25, "Nombre": "IPC"}])
    )
    ops = Client().get_operacion("IPC")
    assert route.called
    assert isinstance(ops[0], Operacion)
    assert ops[0].id == 25
    assert ops[0].nombre == "IPC"


@respx.mock
def test_get_operacion_forwards_det_param():
    route = respx.get(f"{BASE}/wstempus/js/ES/OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[{"Id": 25, "Nombre": "IPC"}])
    )
    Client().get_operacion("IPC", det="2")
    assert route.calls.last.request.url.params["det"] == "2"


@respx.mock
def test_get_operacion_no_query_when_det_none():
    route = respx.get(f"{BASE}/wstempus/js/ES/OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[{"Id": 25, "Nombre": "IPC"}])
    )
    Client().get_operacion("IPC")
    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
def test_get_operacion_raw_returns_dict():
    respx.get(f"{BASE}/wstempus/js/ES/OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[{"Id": 25, "Nombre": "IPC"}])
    )
    data = Client().get_operacion("IPC", raw=True)
    assert data == [{"Id": 25, "Nombre": "IPC"}]


# --------------------------------------------------------------- get_datos_serie
@respx.mock
def test_get_datos_serie_hits_path_with_id():
    route = respx.get(f"{BASE}/wstempus/js/ES/DATOS_SERIE/CP0222024").mock(
        return_value=httpx.Response(200, json=[{"Cod": "CP0222024", "Nombre": "S", "Data": []}])
    )
    series = Client().get_datos_serie("CP0222024")
    assert route.called
    assert isinstance(series[0], DatosSerie)
    assert series[0].cod == "CP0222024"


@respx.mock
def test_get_datos_serie_forwards_scalar_params():
    route = respx.get(f"{BASE}/wstempus/js/ES/DATOS_SERIE/CP0222024").mock(
        return_value=httpx.Response(200, json=[{"Cod": "CP0222024", "Nombre": "S", "Data": []}])
    )
    Client().get_datos_serie("CP0222024", nult=12, det="1", tip="AM")
    params = route.calls.last.request.url.params
    assert params["nult"] == "12"
    assert params["det"] == "1"
    assert params["tip"] == "AM"


@respx.mock
def test_get_datos_serie_forwards_date_as_repeated_query():
    route = respx.get(f"{BASE}/wstempus/js/ES/DATOS_SERIE/CP0222024").mock(
        return_value=httpx.Response(200, json=[{"Cod": "CP0222024", "Nombre": "S", "Data": []}])
    )
    # httpx serializa la lista como claves repetidas en la query
    Client().get_datos_serie("CP0222024", date=["20200101:20201231", "20210101:20211231"])
    assert route.calls.last.request.url.params.get_list("date") == [
        "20200101:20201231",
        "20210101:20211231",
    ]


@respx.mock
def test_get_datos_serie_raw():
    respx.get(f"{BASE}/wstempus/js/ES/DATOS_SERIE/CP0222024").mock(
        return_value=httpx.Response(200, json=[{"Data": []}])
    )
    data = Client().get_datos_serie("CP0222024", raw=True)
    assert data == [{"Data": []}]


# -------------------------------------------------- get_datos_metadataoperacion
@respx.mock
def test_get_datos_metadataoperacion_hits_path_with_op():
    route = respx.get(f"{BASE}/wstempus/js/ES/DATOS_METADATAOPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[{"Cod": "S1", "Nombre": "S", "Data": []}])
    )
    series = Client().get_datos_metadataoperacion("IPC", nult=1)
    assert route.called
    assert isinstance(series[0], DatosSerie)
    assert series[0].cod == "S1"


@respx.mock
def test_get_datos_metadataoperacion_compiles_filtros_to_g():
    route = respx.get(f"{BASE}/wstempus/js/ES/DATOS_METADATAOPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[{"Cod": "S1", "Nombre": "S", "Data": []}])
    )
    Client().get_datos_metadataoperacion(
        "IPC",
        p="12",
        filtros=[("115", ["29", "30"]), ("3", ["84"])],
    )
    params = route.calls.last.request.url.params
    assert params["p"] == "12"
    # OR dentro del grupo -> g1 con valores repetidos; AND entre grupos -> g2
    assert params.get_list("g1") == ["115:29", "115:30"]
    assert params["g2"] == "3:84"


@respx.mock
def test_get_datos_metadataoperacion_no_filtros_means_no_g():
    route = respx.get(f"{BASE}/wstempus/js/ES/DATOS_METADATAOPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[{"Cod": "S1", "Nombre": "S", "Data": []}])
    )
    Client().get_datos_metadataoperacion("IPC")
    params = dict(route.calls.last.request.url.params)
    assert not any(k.startswith("g") for k in params)


@respx.mock
def test_get_datos_metadataoperacion_raw():
    respx.get(f"{BASE}/wstempus/js/ES/DATOS_METADATAOPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[{"Data": []}])
    )
    data = Client().get_datos_metadataoperacion("IPC", raw=True)
    assert data == [{"Data": []}]
