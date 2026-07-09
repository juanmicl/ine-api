from ine._urls import (
    build_params,
    datos_tabla_path,
    operaciones_path,
    tablas_operacion_path,
)


def test_paths():
    assert operaciones_path("ES") == "/wstempus/js/ES/OPERACIONES_DISPONIBLES"
    assert tablas_operacion_path("ES", "IPC") == "/wstempus/js/ES/TABLAS_OPERACION/IPC"
    assert datos_tabla_path("EN", "24077") == "/wstempus/js/EN/DATOS_TABLA/24077"


def test_build_params_drops_none():
    assert build_params(det="1", nult=12) == {"det": "1", "nult": 12}
    assert build_params() == {}
