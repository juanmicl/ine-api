# tests/test_dataframe.py
"""Tests de ``DatosSerie.to_dataframe()`` (extra ``ine-api[dataframe]``).

Se omiten todos los tests si pandas no está instalado (``importorskip``),
salvo el de ImportError que simula su ausancia vía monkeypatch.
"""

import sys

import httpx
import pytest
import respx

from ine.client import Client
from ine.models.datos import DatosSerie

pd = pytest.importorskip("pandas")  # noqa: N816 — skipa el módulo sin pandas

BASE = "https://servicios.ine.es"
JS = f"{BASE}/wstempus/js/ES"

_PAYLOAD = {
    "COD": "CP0222024",
    "Nombre": "IPC General",
    "Data": [
        {"Fecha": 1293840000000, "Valor": 0.5, "Anyo": 2011, "FK_Periodo": 1, "Secreto": False},
        {"Fecha": 1296518400000, "Valor": 0.3, "Anyo": 2011, "FK_Periodo": 2, "Secreto": False},
        {"Fecha": 1298937600000, "Valor": 0.7, "Anyo": 2011, "FK_Periodo": 3, "Secreto": True},
    ],
}


def _serie() -> DatosSerie:
    return DatosSerie.model_validate(_PAYLOAD)


# ================================================================ to_dataframe
def test_to_dataframe_returns_dataframe():
    df = _serie().to_dataframe()
    assert isinstance(df, pd.DataFrame)


def test_to_dataframe_columns():
    df = _serie().to_dataframe()
    assert list(df.columns) == ["fecha", "valor", "anyo", "fk_periodo", "secreto"]


def test_to_dataframe_row_count():
    df = _serie().to_dataframe()
    assert len(df) == 3


def test_to_dataframe_values():
    df = _serie().to_dataframe()
    assert df.iloc[0]["valor"] == 0.5
    assert bool(df.iloc[2]["secreto"])  # numpy.bool_ → Python bool
    assert df.iloc[1]["fk_periodo"] == 2


def test_to_dataframe_fecha_is_datetime():
    df = _serie().to_dataframe()
    assert pd.api.types.is_datetime64_any_dtype(df["fecha"])


# ================================================================ ImportError path
def test_to_dataframe_raises_without_pandas(monkeypatch):
    """Sin pandas → ImportError con pista de instalación."""
    monkeypatch.setitem(sys.modules, "pandas", None)
    with pytest.raises(ImportError, match="ine-api\\[dataframe\\]"):
        _serie().to_dataframe()


# ================================================================ end-to-end
@respx.mock
def test_end_to_end_datos_serie_to_dataframe():
    respx.get(f"{JS}/DATOS_SERIE/53262").mock(return_value=httpx.Response(200, json=[_PAYLOAD]))
    series = Client(retries=0).datos.serie("53262")
    df = series[0].to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert df.iloc[0]["valor"] == 0.5
