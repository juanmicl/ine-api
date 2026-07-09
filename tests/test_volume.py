# tests/test_volume.py
"""Tests de INEVolumeError: detección del objeto ``{"status": "..."}`` de volumen.

El INE devuelve ``200`` con un objeto ``{"status": "...restricciones de
volumen..."}`` cuando una tabla es demasiado grande para la API JSON. Se
intercepta en ``Backend._request`` (antes del *guard* de forma de ``get_list``)
para que el usuario reciba un ``INEVolumeError`` claro que sugiera
``Client.download_table`` en vez de un confuso ``INEParseError``.
"""

import httpx
import pytest
import respx

from ine._backend import Backend
from ine._config import Config
from ine.client import Client
from ine.errors import INEError, INELogicalError, INEParseError, INEVolumeError

_BASE = "https://servicios.ine.es/wstempus/js/ES"
_STATUS_BODY = {"status": "No puede mostrarse por restricciones de volumen"}


def _backend() -> Backend:
    # retries=0: no verificamos reintentos aquí.
    return Backend(Config(retries=0))


def test_ine_volume_error_is_logical_error():
    # INEVolumeError hereda de INELogicalError: un `except INELogicalError` la captura.
    assert issubclass(INEVolumeError, INELogicalError)
    assert issubclass(INEVolumeError, INEError)


@respx.mock
def test_volume_dict_raises_ine_volume_error_from_get_list():
    # get_list sobre un 200 con {"status": "..."} → INEVolumeError (no INEParseError).
    respx.get(f"{_BASE}/DATOS_TABLA/68535").mock(
        return_value=httpx.Response(200, json=_STATUS_BODY)
    )
    with pytest.raises(INEVolumeError) as exc:
        _backend().get_list("/wstempus/js/ES/DATOS_TABLA/68535")
    # El mensaje incluye el status del INE y la sugerencia de download_table.
    msg = str(exc.value).lower()
    assert "volumen" in msg
    assert "download_table" in msg


@respx.mock
def test_volume_dict_via_client_get_datos_tabla():
    # Flujo completo de cliente: get_datos_tabla propaga INEVolumeError.
    respx.get(f"{_BASE}/DATOS_TABLA/68535").mock(
        return_value=httpx.Response(200, json=_STATUS_BODY)
    )
    with pytest.raises(INEVolumeError):
        Client(retries=0).get_datos_tabla("68535")


@respx.mock
def test_volume_error_caught_by_logical_error():
    # Sigue siendo capturable por el handler genérico `except INELogicalError`.
    respx.get(f"{_BASE}/DATOS_TABLA/68535").mock(
        return_value=httpx.Response(200, json=_STATUS_BODY)
    )
    with pytest.raises(INELogicalError):
        Client(retries=0).get_datos_tabla("68535")


@respx.mock
def test_volume_dict_raises_before_parse_error():
    # Sin la intercepción, get_list vería un dict y lanzaría INEParseError:
    # comprobamos que NO es INEParseError sino su subclase más específica.
    respx.get(f"{_BASE}/DATOS_TABLA/68535").mock(
        return_value=httpx.Response(200, json=_STATUS_BODY)
    )
    with pytest.raises(INEVolumeError):
        _backend().get_list("/wstempus/js/ES/DATOS_TABLA/68535")


@respx.mock
def test_dict_without_status_not_misclassified():
    # Un dict legítimo sin "status" (get_one) no se confunde con volumen.
    respx.get(f"{_BASE}/ESCALA/1").mock(
        return_value=httpx.Response(200, json={"Id": 1, "Nombre": "x"})
    )
    data = _backend().get_one("/wstempus/js/ES/ESCALA/1")
    assert data == {"Id": 1, "Nombre": "x"}


@respx.mock
def test_dict_without_status_to_get_list_still_parse_error():
    # Un dict sin "status" que llega a get_list sigue siendo INEParseError.
    respx.get(f"{_BASE}/X").mock(return_value=httpx.Response(200, json={"Id": 1}))
    with pytest.raises(INEParseError):
        _backend().get_list("/wstempus/js/ES/X")


@respx.mock
def test_list_response_not_affected_by_volume_check():
    # Una lista normal pasa de largo: el chequeo sólo mira dicts con "status".
    respx.get(f"{_BASE}/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=[{"Id": 4, "Nombre": "Op"}])
    )
    data = _backend().get_list("/wstempus/js/ES/OPERACIONES_DISPONIBLES")
    assert data == [{"Id": 4, "Nombre": "Op"}]
