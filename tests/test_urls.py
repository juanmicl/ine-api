from ine._urls import (
    build_params,
    datos_metadataoperacion_path,
    datos_serie_path,
    datos_tabla_path,
    operacion_path,
    operaciones_path,
    serie_metadataoperacion_path,
    serie_path,
    series_operacion_path,
    series_tabla_path,
    tablas_operacion_path,
    valores_serie_path,
)


def test_paths():
    assert operaciones_path("ES") == "/wstempus/js/ES/OPERACIONES_DISPONIBLES"
    assert tablas_operacion_path("ES", "IPC") == "/wstempus/js/ES/TABLAS_OPERACION/IPC"
    assert datos_tabla_path("EN", "24077") == "/wstempus/js/EN/DATOS_TABLA/24077"


def test_operacion_and_datos_serie_paths():
    assert operacion_path("ES", "IPC") == "/wstempus/js/ES/OPERACION/IPC"
    assert datos_serie_path("ES", "CP0222024") == "/wstempus/js/ES/DATOS_SERIE/CP0222024"


def test_datos_metadataoperacion_path():
    assert datos_metadataoperacion_path("ES", "IPC") == (
        "/wstempus/js/ES/DATOS_METADATAOPERACION/IPC"
    )
    assert datos_metadataoperacion_path("EN", "CIFRA") == (
        "/wstempus/js/EN/DATOS_METADATAOPERACION/CIFRA"
    )


def test_build_params_drops_none():
    assert build_params(det="1", nult=12) == {"det": "1", "nult": 12}
    assert build_params() == {}


def test_series_paths():
    assert series_operacion_path("ES", "IPC") == "/wstempus/js/ES/SERIES_OPERACION/IPC"
    assert serie_path("ES", "CP0222024") == "/wstempus/js/ES/SERIE/CP0222024"
    assert serie_path("EN", "12345") == "/wstempus/js/EN/SERIE/12345"
    assert series_tabla_path("ES", "24077") == "/wstempus/js/ES/SERIES_TABLA/24077"
    assert valores_serie_path("ES", "CP0222024") == "/wstempus/js/ES/VALORES_SERIE/CP0222024"


def test_serie_metadataoperacion_path():
    assert serie_metadataoperacion_path("ES", "IPC") == (
        "/wstempus/js/ES/SERIE_METADATAOPERACION/IPC"
    )
    assert serie_metadataoperacion_path("EN", "CIFRA") == (
        "/wstempus/js/EN/SERIE_METADATAOPERACION/CIFRA"
    )
