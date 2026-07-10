# ine/services/__init__.py
"""Servicios por dominio para :class:`~ine.client.Client` / :class:`~ine.async_client.AsyncClient`.

Cada servicio agrupa los endpoints de un dominio (operaciones, series, datos,
tablas) y se instancian como atributos del cliente:

    >>> client = Client()
    >>> client.operaciones.list()        # operaciones estadísticas
    >>> client.series.get("CP0222024")   # ficha de una serie
    >>> client.datos.serie("53262")      # observaciones de una serie
    >>> client.tablas.by_operacion("IPC")  # tablas de una operación
"""

from ine.services.datos import AsyncDatosService, DatosService
from ine.services.maestros import AsyncMaestrosService, MaestrosService
from ine.services.operaciones import AsyncOperacionesService, OperacionesService
from ine.services.publicaciones import AsyncPublicacionesService, PublicacionesService
from ine.services.series import AsyncSeriesService, SeriesService
from ine.services.tablas import AsyncTablasService, TablasService
from ine.services.valores import AsyncValoresService, ValoresService
from ine.services.variables import AsyncVariablesService, VariablesService

__all__ = [
    "AsyncDatosService",
    "AsyncMaestrosService",
    "AsyncOperacionesService",
    "AsyncPublicacionesService",
    "AsyncSeriesService",
    "AsyncTablasService",
    "AsyncValoresService",
    "AsyncVariablesService",
    "DatosService",
    "MaestrosService",
    "OperacionesService",
    "PublicacionesService",
    "SeriesService",
    "TablasService",
    "ValoresService",
    "VariablesService",
]
