# tests/test_models_datos.py
from datetime import UTC, datetime

from ine.models.datos import DatosObservacion, DatosSerie


def test_datos_observacion_fecha_epoch():
    o = DatosObservacion.model_validate(
        {
            "Fecha": 1293840000000,
            "Valor": 1.5,
            "Anyo": 2011,
            "FK_Periodo": 1,
        }
    )
    assert o.fecha == datetime(2011, 1, 1, tzinfo=UTC)
    assert o.valor == 1.5
    assert o.secreto is False


def test_datos_serie_nested():
    s = DatosSerie.model_validate(
        {
            "COD": "IPC53262",
            "Nombre": "n",
            "Data": [{"Fecha": 1293840000000, "Valor": 0.1, "Anyo": 2011, "FK_Periodo": 1}],
        }
    )
    assert s.cod == "IPC53262"
    assert len(s.data) == 1
    assert isinstance(s.data[0].fecha, datetime)
