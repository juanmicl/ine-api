# tests/test_contract.py
import httpx

from ine.client import Client

BASE = "https://servicios.ine.es/wstempus/js/ES"


def test_contract_operaciones(mock_ine):
    mock_ine.get(f"{BASE}/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "Id": 4,
                    "Cod_IOE": "30147",
                    "Nombre": "Estadística de Efectos de Comercio Impagados",
                    "Codigo": "ECE",
                    "Url": "https://...",
                }
            ],
        )
    )
    ops = Client().get_operaciones(raw=True)
    assert ops[0]["Id"] == 4
    assert ops[0]["Codigo"] == "ECE"


def test_contract_tablas(mock_ine):
    mock_ine.get(f"{BASE}/TABLAS_OPERACION/IPC").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "Id": 24077,
                    "Nombre": "Índice general nacional",
                    "Codigo": "NAC",
                    "FK_Periodicidad": 1,
                }
            ],
        )
    )
    tablas = Client().get_tablas("IPC")
    assert tablas[0]["Id"] == 24077


def test_contract_datos_tabla(mock_ine):
    mock_ine.get(f"{BASE}/DATOS_TABLA/24077").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "COD": "IPC53262",
                    "Nombre": "Serie",
                    "Data": [{"Fecha": 1293840000000, "Valor": 0.5, "Anyo": 2011, "FK_Periodo": 1}],
                }
            ],
        )
    )
    datos = Client().get_datos_tabla("24077", raw=True)
    assert datos[0]["COD"] == "IPC53262"
    assert datos[0]["Data"][0]["Anyo"] == 2011
