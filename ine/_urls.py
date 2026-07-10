from __future__ import annotations

from typing import Any


def operaciones_path(lang: str) -> str:
    return f"/wstempus/js/{lang}/OPERACIONES_DISPONIBLES"


def operacion_path(lang: str, op: str) -> str:
    return f"/wstempus/js/{lang}/OPERACION/{op}"


def tablas_operacion_path(lang: str, op: str) -> str:
    return f"/wstempus/js/{lang}/TABLAS_OPERACION/{op}"


def datos_tabla_path(lang: str, tabla_id: str) -> str:
    return f"/wstempus/js/{lang}/DATOS_TABLA/{tabla_id}"


def datos_serie_path(lang: str, serie_id: str) -> str:
    return f"/wstempus/js/{lang}/DATOS_SERIE/{serie_id}"


def datos_metadataoperacion_path(lang: str, op: str) -> str:
    return f"/wstempus/js/{lang}/DATOS_METADATAOPERACION/{op}"


def series_operacion_path(lang: str, op: str) -> str:
    return f"/wstempus/js/{lang}/SERIES_OPERACION/{op}"


def serie_path(lang: str, serie_id: str) -> str:
    return f"/wstempus/js/{lang}/SERIE/{serie_id}"


def series_tabla_path(lang: str, tabla_id: str) -> str:
    return f"/wstempus/js/{lang}/SERIES_TABLA/{tabla_id}"


def valores_serie_path(lang: str, serie_id: str) -> str:
    return f"/wstempus/js/{lang}/VALORES_SERIE/{serie_id}"


def serie_metadataoperacion_path(lang: str, op: str) -> str:
    return f"/wstempus/js/{lang}/SERIE_METADATAOPERACION/{op}"


# --- MAESTROS ---


def escalas_path(lang: str) -> str:
    return f"/wstempus/js/{lang}/ESCALAS"


def escala_path(lang: str, escala_id: int) -> str:
    return f"/wstempus/js/{lang}/ESCALA/{escala_id}"


def unidades_path(lang: str) -> str:
    return f"/wstempus/js/{lang}/UNIDADES"


def unidad_path(lang: str, unidad_id: int) -> str:
    return f"/wstempus/js/{lang}/UNIDAD/{unidad_id}"


def unidades_operacion_path(lang: str, op: str) -> str:
    return f"/wstempus/js/{lang}/UNIDADES_OPERACION/{op}"


def periodo_path(lang: str, periodo_id: int) -> str:
    return f"/wstempus/js/{lang}/PERIODO/{periodo_id}"


def periodicidades_path(lang: str) -> str:
    return f"/wstempus/js/{lang}/PERIODICIDADES"


def periodicidad_path(lang: str, periodicidad_id: int) -> str:
    return f"/wstempus/js/{lang}/PERIODICIDAD/{periodicidad_id}"


def clasificaciones_path(lang: str) -> str:
    return f"/wstempus/js/{lang}/CLASIFICACIONES"


def clasificaciones_operacion_path(lang: str, op: str) -> str:
    return f"/wstempus/js/{lang}/CLASIFICACIONES_OPERACION/{op}"


def build_params(**kwargs: Any) -> dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v is not None}
