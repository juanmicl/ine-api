# tests/test_namespaces_params.py
"""Reenvío de query params para los 3 métodos con firma ampliada del refactor R1.

``operaciones.list``, ``tablas.by_operacion`` y ``datos.tabla`` ganaron parámetros
que no existían en los métodos planos originales. Como usan ``build_params(**kwargs)``
(que filtra ``None`` silenciosamente), un *typo* en una clave hararía el param sin
error. Estos tests confirman que cada param llega al query string de la petición.
"""

import httpx
import respx

from ine.client import Client

BASE = "https://servicios.ine.es"


@respx.mock
def test_operaciones_list_forwards_det_geo_page():
    route = respx.get(f"{BASE}/wstempus/js/ES/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=[{"Id": 4, "Nombre": "Op"}])
    )
    Client().operaciones.list(det="1", geo="1", page=2)
    params = route.calls.last.request.url.params
    assert params["det"] == "1"
    assert params["geo"] == "1"
    assert params["page"] == "2"


@respx.mock
def test_tablas_by_operacion_forwards_det_geo_tip():
    route = respx.get(f"{BASE}/wstempus/js/ES/TABLAS_OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[{"Id": 1, "Nombre": "T"}])
    )
    Client().tablas.by_operacion("IPC", det="1", geo="0", tip="M")
    params = route.calls.last.request.url.params
    assert params["det"] == "1"
    assert params["geo"] == "0"
    assert params["tip"] == "M"


@respx.mock
def test_datos_tabla_forwards_scalar_and_list_params():
    route = respx.get(f"{BASE}/wstempus/js/ES/DATOS_TABLA/24077").mock(
        return_value=httpx.Response(200, json=[{"Cod": "T24077", "Nombre": "T", "Data": []}])
    )
    Client().datos.tabla(
        "24077", nult=12, det="1", tip="AM", tv=["115:29"], date=["20200101:20210101"]
    )
    params = route.calls.last.request.url.params
    # Escalares
    assert params["nult"] == "12"
    assert params["det"] == "1"
    assert params["tip"] == "AM"
    # Listas → claves repetidas en la query
    assert params.get_list("tv") == ["115:29"]
    assert params.get_list("date") == ["20200101:20210101"]
