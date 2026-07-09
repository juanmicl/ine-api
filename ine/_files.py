# ine/_files.py
"""Servicio de ficheros del INE (CSV / PC-Axis / XLSX).

Atención: este servicio vive en un host DISTINTO al de la API Tempus JSON:
``https://www.ine.es/jaxiT3/files`` frente a ``https://servicios.ine.es/wstempus``.
Las URLs que construye :func:`build_file_url` son absolutas, así que ignoran el
``base_url`` configurado en el cliente (el ``httpx_client`` reutilizado hereda
su transporte/reintentos, pero la URL absoluta anula la base de Tempus).
"""

from __future__ import annotations

from enum import StrEnum

#: Host del servicio de ficheros (no es el de la API Tempus JSON).
_FILE_BASE = "https://www.ine.es/jaxiT3/files"


class Format(StrEnum):
    """Formatos de fichero oficiales del INE para una tabla.

    El valor (``"csv_bdsc"``, ``"px"``, ...) es el segmento que aparece en la URL
    de descarga.
    """

    CSV_BDSC = "csv_bdsc"
    CSV_BD = "csv_bd"
    PX = "px"
    XLSX = "xlsx"


# Extensión de fichero por formato: los dos CSV comparten ``.csv``.
_EXT_BY_FORMAT: dict[Format, str] = {
    Format.CSV_BDSC: "csv",
    Format.CSV_BD: "csv",
    Format.PX: "px",
    Format.XLSX: "xlsx",
}


def build_file_url(lang: str, fmt: Format, table_id: str) -> str:
    """Construye la URL absoluta de descarga de un fichero de tabla.

    Forma: ``{base}/t/{lang}/{fmt.value}/{table_id}.{ext}?nocab=1``, donde
    ``ext`` se deriva de ``fmt`` (``csv`` para los ``csv_*``, ``px``, ``xlsx``).

    Args:
        lang: Idioma (segmento ``/t/{lang}/``); p. ej. ``"es"`` o ``"en"``.
        fmt: Formato del fichero.
        table_id: Identificador Tempus3 de la tabla (``Id``).
    """
    ext = _EXT_BY_FORMAT[fmt]
    return f"{_FILE_BASE}/t/{lang}/{fmt.value}/{table_id}.{ext}?nocab=1"
