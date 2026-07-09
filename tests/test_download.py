# tests/test_download.py
"""Tests de Client.download_table / AsyncClient.download_table (servicio de ficheros).

Se mockea la URL del servicio de ficheros con respx. La URL se construye con el
propio ``build_file_url`` (si driftara, el route no casaría y el test fallaría).
"""

from pathlib import Path

import httpx
import pytest
import respx

from ine import Format
from ine._files import build_file_url
from ine.async_client import AsyncClient
from ine.client import Client
from ine.errors import INENotFoundError

_BODY = b"col1;col2\n1;2\n"
_TABLE = "68535"


def _client() -> Client:
    return Client(retries=0)


@respx.mock
def test_download_table_path_writes_file_and_returns_path(tmp_path):
    # path mode: streama por chunks al fichero y devuelve Path apuntando a él.
    url = build_file_url("es", Format.CSV_BDSC, _TABLE)
    respx.get(url).mock(return_value=httpx.Response(200, content=_BODY))

    dest = tmp_path / "padron.csv"
    result = _client().download_table(_TABLE, fmt=Format.CSV_BDSC, path=dest, lang="es")

    assert isinstance(result, Path)
    assert result == dest
    assert dest.read_bytes() == _BODY  # byte-for-byte


@respx.mock
def test_download_table_bytes_returns_body():
    # path=None: devuelve los bytes completos en memoria.
    url = build_file_url("es", Format.CSV_BDSC, _TABLE)
    respx.get(url).mock(return_value=httpx.Response(200, content=_BODY))

    result = _client().download_table(_TABLE, fmt=Format.CSV_BDSC, lang="es")

    assert isinstance(result, bytes)
    assert result == _BODY


@respx.mock
def test_download_table_url_reflects_format_and_lang():
    # El formato y el idioma van en el segmento de la URL.
    c = _client()

    # CSV_BDSC en inglés → /t/en/csv_bdsc/{id}.csv
    route_csv = respx.get(build_file_url("en", Format.CSV_BDSC, _TABLE)).mock(
        return_value=httpx.Response(200, content=_BODY)
    )
    c.download_table(_TABLE, fmt=Format.CSV_BDSC, lang="en")
    csv_url = str(route_csv.calls.last.request.url)
    assert "/t/en/csv_bdsc/" in csv_url
    assert csv_url.endswith(f"{_TABLE}.csv?nocab=1")

    # PX en español → /t/es/px/{id}.px
    route_px = respx.get(build_file_url("es", Format.PX, _TABLE)).mock(
        return_value=httpx.Response(200, content=b"px")
    )
    c.download_table(_TABLE, fmt=Format.PX, lang="es")
    px_url = str(route_px.calls.last.request.url)
    assert "/t/es/px/" in px_url
    assert px_url.endswith(f"{_TABLE}.px?nocab=1")


@respx.mock
def test_download_table_404_raises_not_found():
    respx.get(build_file_url("es", Format.CSV_BDSC, "999999")).mock(
        return_value=httpx.Response(404, text="not found")
    )
    with pytest.raises(INENotFoundError):
        _client().download_table("999999", lang="es")


@respx.mock
@pytest.mark.anyio
async def test_async_download_table_bytes_returns_body():
    url = build_file_url("es", Format.CSV_BDSC, _TABLE)
    respx.get(url).mock(return_value=httpx.Response(200, content=_BODY))

    async with AsyncClient(retries=0) as c:
        result = await c.download_table(_TABLE, fmt=Format.CSV_BDSC, lang="es")

    assert isinstance(result, bytes)
    assert result == _BODY


@respx.mock
@pytest.mark.anyio
async def test_async_download_table_path_writes_file(tmp_path):
    url = build_file_url("es", Format.PX, _TABLE)
    respx.get(url).mock(return_value=httpx.Response(200, content=b"px-content"))

    dest = tmp_path / "padron.px"
    async with AsyncClient(retries=0) as c:
        result = await c.download_table(_TABLE, fmt=Format.PX, path=dest, lang="es")

    assert isinstance(result, Path)
    assert result == dest
    assert dest.read_bytes() == b"px-content"


def test_format_public_reexport():
    from ine import __all__

    assert "Format" in __all__
    assert Format.CSV_BDSC.value == "csv_bdsc"
