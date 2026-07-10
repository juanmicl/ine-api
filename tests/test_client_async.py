# tests/test_client_async.py
import httpx
import pytest
import respx

from ine._config import Lang
from ine.async_client import AsyncClient
from ine.errors import INELogicalError
from ine.models.datos import DatosSerie
from ine.models.operaciones import Operacion


@respx.mock
@pytest.mark.anyio
async def test_async_get_operaciones():
    respx.get("https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=[{"Id": 4, "Nombre": "Op"}])
    )
    async with AsyncClient() as c:
        ops = await c.operaciones.list()
    assert isinstance(ops[0], Operacion)
    assert ops[0].id == 4


@respx.mock
@pytest.mark.anyio
async def test_async_get_operaciones_raw():
    respx.get("https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=[{"Id": 4, "Nombre": "Op"}])
    )
    async with AsyncClient() as c:
        ops = await c.operaciones.list(raw=True)
    assert ops == [{"Id": 4, "Nombre": "Op"}]


@respx.mock
@pytest.mark.anyio
async def test_async_get_tablas_passes_operacion_in_path():
    route = respx.get("https://servicios.ine.es/wstempus/js/ES/TABLAS_OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[{"Id": 1, "Nombre": "T"}])
    )
    async with AsyncClient() as c:
        await c.tablas.by_operacion("IPC")
    assert route.called


@respx.mock
@pytest.mark.anyio
async def test_async_get_datos_tabla_returns_models():
    respx.get("https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/24077").mock(
        return_value=httpx.Response(
            200,
            json=[{"Cod": "S24077", "Nombre": "Serie", "Data": []}],
        )
    )
    async with AsyncClient() as c:
        series = await c.datos.tabla("24077")
    assert isinstance(series[0], DatosSerie)
    assert series[0].cod == "S24077"


@respx.mock
@pytest.mark.anyio
async def test_async_get_datos_tabla_raw():
    respx.get("https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/24077").mock(
        return_value=httpx.Response(200, json=[{"Data": []}])
    )
    async with AsyncClient() as c:
        data = await c.datos.tabla("24077", raw=True)
    assert data == [{"Data": []}]


@pytest.mark.anyio
async def test_async_client_is_context_manager():
    async with AsyncClient() as c:
        assert isinstance(c, AsyncClient)


@pytest.mark.anyio
async def test_async_client_uses_injected_httpx_client():
    injected = httpx.AsyncClient(base_url="https://servicios.ine.es")
    c = AsyncClient(httpx_client=injected)
    assert c._backend._client is injected
    await injected.aclose()


@respx.mock
@pytest.mark.anyio
async def test_async_client_lang_en_in_path():
    route = respx.get("https://servicios.ine.es/wstempus/js/EN/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=[])
    )
    async with AsyncClient(lang=Lang.EN) as c:
        await c.operaciones.list()
    assert route.called


@respx.mock
@pytest.mark.anyio
async def test_async_client_propagates_logical_error():
    respx.get("https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json="La operación indicada no existe (X)")
    )
    with pytest.raises(INELogicalError):
        async with AsyncClient() as c:
            await c.operaciones.list()


@respx.mock
@pytest.mark.anyio
async def test_async_get_datos_metadataoperacion_compiles_filtros_to_g():
    route = respx.get("https://servicios.ine.es/wstempus/js/ES/DATOS_METADATAOPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[{"Cod": "S1", "Nombre": "S", "Data": []}])
    )
    async with AsyncClient() as c:
        await c.datos.metadata_operacion("IPC", filtros=[("115", ["29", "30"]), ("3", ["84"])])
    params = route.calls.last.request.url.params
    # OR dentro del grupo -> g1 repetido; AND entre grupos -> g2
    assert params.get_list("g1") == ["115:29", "115:30"]
    assert params["g2"] == "3:84"
