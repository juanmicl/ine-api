# tests/test_models_base.py
from datetime import UTC, datetime

from ine.models._base import ConFecha, _BaseModel


def test_hard_ine_keys_acronyms_and_camelcase():
    from ine.models._base import _BaseModel

    class M(_BaseModel):
        cod_ioe: str | None = None
        fk_pub_fecha_act: int | None = None
        anyo_periodo_ini: str | None = None
        t3_tipo_dato: str | None = None

    m = M.model_validate(
        {
            "Cod_IOE": "30138",
            "FK_PubFechaAct": 12597,
            "Anyo_Periodo_ini": "1961",
            "T3_TipoDato": "P",
        }
    )
    assert m.cod_ioe == "30138"
    assert m.fk_pub_fecha_act == 12597
    assert m.anyo_periodo_ini == "1961"
    assert m.t3_tipo_dato == "P"


def test_simple_keys_and_populate_by_name():
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
