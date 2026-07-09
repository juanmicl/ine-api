# tests/test_backend.py
import httpx
import pytest
import respx

from ine._backend import AsyncBackend, Backend
from ine._config import Config
from ine.errors import (
    INEConnectionError,
    INEHTTPError,
    INELogicalError,
    INENotFoundError,
    INEParseError,
)


def make_backend():
    # retries=0: estos tests verifican la traducción de errores (H2/H3), no los
    # reintentos (que se cubren en tests/test_retries.py). Sin esto, un 500 o un
    # ConnectError dispararía 3 reintentos con sleeps reales de backoff.
    return Backend(Config(retries=0))


@respx.mock
def test_get_list_returns_list():
    respx.get("https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=[{"Id": 4, "Nombre": "Op"}])
    )
    data = make_backend().get_list("/wstempus/js/ES/OPERACIONES_DISPONIBLES")
    assert data == [{"Id": 4, "Nombre": "Op"}]


@respx.mock
def test_get_list_translates_404():
    respx.get("https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/0").mock(
        return_value=httpx.Response(404, text="<html>404</html>")
    )
    with pytest.raises(INENotFoundError):
        make_backend().get_list("/wstempus/js/ES/DATOS_SERIE/0")


@respx.mock
def test_get_list_translates_500():
    respx.get("https://servicios.ine.es/wstempus/js/ES/X").mock(
        return_value=httpx.Response(500, text="err")
    )
    with pytest.raises(INEHTTPError) as exc:
        make_backend().get_list("/wstempus/js/ES/X")
    assert not isinstance(exc.value, INENotFoundError)


@respx.mock
def test_get_list_raises_logical_error_on_200_string_body():
    respx.get("https://servicios.ine.es/wstempus/js/ES/GRUPOS").mock(
        return_value=httpx.Response(200, json="La operación indicada no existe (GRUPOS)")
    )
    with pytest.raises(INELogicalError):
        make_backend().get_list("/wstempus/js/ES/GRUPOS")


@respx.mock
def test_get_list_raises_parse_error_on_html_200():
    respx.get("https://servicios.ine.es/wstempus/js/ES/X").mock(
        return_value=httpx.Response(
            200, text="<html>oops</html>", headers={"content-type": "text/html"}
        )
    )
    with pytest.raises(INEParseError):
        make_backend().get_list("/wstempus/js/ES/X")


@respx.mock
def test_get_list_raises_parse_error_on_empty_body():
    # El INE puede devolver 200 con content-type application/json pero cuerpo
    # vacío: response.json() lanza JSONDecodeError, que debe traducirse a
    # INEParseError (no filtrar la excepción cruda de la librería stdlib).
    respx.get("https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/0").mock(
        return_value=httpx.Response(200, content="", headers={"content-type": "application/json"})
    )
    with pytest.raises(INEParseError):
        make_backend().get_list("/wstempus/js/ES/DATOS_SERIE/0")


@respx.mock
def test_get_list_raises_parse_error_on_malformed_json():
    # 200 con content-type application/json pero JSON inválido: mismo contrato,
    # debe traducirse a INEParseError.
    respx.get("https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/0").mock(
        return_value=httpx.Response(
            200, content="{not json", headers={"content-type": "application/json"}
        )
    )
    with pytest.raises(INEParseError):
        make_backend().get_list("/wstempus/js/ES/DATOS_SERIE/0")


@respx.mock
def test_get_list_translates_connection_error():
    respx.get("https://servicios.ine.es/wstempus/js/ES/X").mock(
        side_effect=httpx.ConnectError("boom")
    )
    with pytest.raises(INEConnectionError):
        make_backend().get_list("/wstempus/js/ES/X")


@respx.mock
def test_get_list_sends_params():
    route = respx.get("https://servicios.ine.es/wstempus/js/ES/X").mock(
        return_value=httpx.Response(200, json=[])
    )
    make_backend().get_list("/wstempus/js/ES/X", params={"det": "1", "page": 2})
    assert route.calls.last.request.url.params["det"] == "1"
    assert route.calls.last.request.url.params["page"] == "2"


@respx.mock
def test_get_list_raises_parse_error_on_dict():
    # Un endpoint de lista debe devolver array; si viene un dict, es un error de parseo.
    respx.get("https://servicios.ine.es/wstempus/js/ES/X").mock(
        return_value=httpx.Response(200, json={"Id": 1})
    )
    with pytest.raises(INEParseError):
        make_backend().get_list("/wstempus/js/ES/X")


@respx.mock
def test_get_one_raises_parse_error_on_list():
    # Un endpoint de recurso único debe devolver un objeto; si viene una lista, es error.
    respx.get("https://servicios.ine.es/wstempus/js/ES/X").mock(
        return_value=httpx.Response(200, json=[{"Id": 1}])
    )
    with pytest.raises(INEParseError):
        make_backend().get_one("/wstempus/js/ES/X")


@respx.mock
def test_get_one_returns_dict():
    respx.get("https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES/4").mock(
        return_value=httpx.Response(200, json={"Id": 4, "Nombre": "Op"})
    )
    data = make_backend().get_one("/wstempus/js/ES/OPERACIONES_DISPONIBLES/4")
    assert data == {"Id": 4, "Nombre": "Op"}


def test_backend_follows_redirects_from_config(monkeypatch):
    seen = {}
    real_init = httpx.Client.__init__

    def spy(self, *a, **kw):
        seen["follow_redirects"] = kw.get("follow_redirects")
        return real_init(self, *a, **kw)

    monkeypatch.setattr(httpx.Client, "__init__", spy)
    Backend(Config(follow_redirects=True))
    assert seen["follow_redirects"] is True


# --- stream() (servicio de ficheros) ---------------------------------------


@respx.mock
def test_stream_yields_iterable_body():
    # 200: cede una response cuyo iter_bytes() produce el body completo.
    respx.get("https://www.ine.es/f/x").mock(return_value=httpx.Response(200, content=b"abc123"))
    backend = make_backend()
    with backend.stream("https://www.ine.es/f/x") as response:
        body = b"".join(response.iter_bytes())
    assert body == b"abc123"


@respx.mock
def test_stream_404_raises_before_yielding_body():
    # 404: _raise_for_status corre ANTES del yield → INENotFoundError, sin body.
    respx.get("https://www.ine.es/f/x").mock(return_value=httpx.Response(404, text="nope"))
    backend = make_backend()
    with pytest.raises(INENotFoundError), backend.stream("https://www.ine.es/f/x") as response:
        response.iter_bytes()  # no debe llegarse aquí  # pragma: no cover


@respx.mock
def test_stream_translates_connection_error():
    # Error de red al abrir el stream → INEConnectionError.
    respx.get("https://www.ine.es/f/x").mock(side_effect=httpx.ConnectError("boom"))
    backend = make_backend()
    with pytest.raises(INEConnectionError), backend.stream("https://www.ine.es/f/x"):
        pass  # pragma: no cover


@respx.mock
@pytest.mark.anyio
async def test_async_stream_yields_iterable_body():
    # Espejo async: aiter_bytes() produce el body completo.
    respx.get("https://www.ine.es/f/x").mock(return_value=httpx.Response(200, content=b"xyz789"))
    backend = AsyncBackend(Config(retries=0))
    async with backend.stream("https://www.ine.es/f/x") as response:
        chunks = [chunk async for chunk in response.aiter_bytes()]
    assert b"".join(chunks) == b"xyz789"
