# tests/test_models_operaciones.py
import httpx

from ine.client import Client
from ine.models.operaciones import Operacion

BASE = "https://servicios.ine.es/wstempus/js/ES"


def test_operacion_model_aliases():
    op = Operacion.model_validate(
        {
            "Id": 4,
            "Cod_IOE": "30147",
            "Nombre": "Efectos impagados",
            "Codigo": "ECE",
        }
    )
    assert op.id == 4
    assert op.cod_ioe == "30147"
    assert op.nombre == "Efectos impagados"
    assert op.codigo == "ECE"


def test_operacion_cod_ioe_optional_empty():
    op = Operacion.model_validate({"Nombre": "X", "Codigo": "Y", "Cod_IOE": ""})
    assert op.cod_ioe == ""


def test_client_get_operaciones_returns_models(mock_ine):
    mock_ine.get(f"{BASE}/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(
            200, json=[{"Id": 4, "Nombre": "n", "Codigo": "c", "Cod_IOE": "i"}]
        )
    )
    ops = Client().get_operaciones()
    assert isinstance(ops[0], Operacion)
    assert ops[0].id == 4


def test_client_get_operaciones_raw(mock_ine):
    payload = [{"Id": 4, "Nombre": "n", "Codigo": "c"}]
    mock_ine.get(f"{BASE}/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=payload)
    )
    ops = Client().get_operaciones(raw=True)
    assert ops == payload
