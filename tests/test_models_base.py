# tests/test_models_base.py
from datetime import UTC, datetime

from ine.models._base import ConFecha, _BaseModel, to_ine_alias


def test_to_ine_alias():
    assert to_ine_alias("fk_periodicidad") == "FK_Periodicidad"
    assert to_ine_alias("t3_operacion") == "T3_Operacion"
    assert to_ine_alias("fecha") == "Fecha"
    assert to_ine_alias("nombre") == "Nombre"


def test_alias_to_snake_and_populate_by_name():
    class M(_BaseModel):
        fk_periodicidad: int
        t3_operacion: str

    m = M.model_validate({"FK_Periodicidad": 1, "T3_Operacion": "IPC"})
    assert m.fk_periodicidad == 1
    assert m.t3_operacion == "IPC"
    # también acepta el nombre pythonic
    m2 = M(fk_periodicidad=2, t3_operacion="X")
    assert m2.fk_periodicidad == 2


def test_extra_ignored():
    class M(_BaseModel):
        nombre: str

    m = M.model_validate({"Nombre": "x", "CampoRaroQueNoExiste": 123})
    assert m.nombre == "x"


def test_fecha_epoch_ms_to_datetime():
    class M(ConFecha):
        fecha: datetime

    m = M.model_validate({"Fecha": 1293840000000})
    assert m.fecha == datetime(2011, 1, 1, tzinfo=UTC)
