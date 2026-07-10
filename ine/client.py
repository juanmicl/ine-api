# ine/client.py
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import httpx

from ine._backend import Backend
from ine._cache import Cache
from ine._config import Config
from ine._config import Lang as Lang
from ine._files import Format, build_file_url
from ine.services import (
    DatosService,
    MaestrosService,
    OperacionesService,
    PublicacionesService,
    SeriesService,
    TablasService,
    VariablesService,
)


class Client:
    """Cliente síncrono para la API Tempus del INE.

    Punto de entrada de la librería. Los endpoints se organizan en **namespaces
    por dominio**, expuestos como atributos del cliente:

        with Client() as c:
            ops = c.operaciones.list()             # operaciones estadísticas
            serie = c.series.get("CP0222024")      # ficha de una serie
            datos = c.datos.serie("53262")         # observaciones de una serie
            tablas = c.tablas.by_operacion("IPC")  # tablas de una operación

    La descarga de ficheros oficiales (CSV / PC-Axis / XLSX) queda en la raíz
    del cliente, al ser un servicio distinto:

        c.download_table("68535", fmt=Format.CSV_BDSC)

    Todos los parámetros del constructor son *keyword-only* para favorecer la
    estabilidad de la firma entre versiones.

    Inyección de dependencias: si se pasa ``httpx_client`` (un
    :class:`httpx.Client` ya configurado), el Backend lo reutiliza tal cual y no
    aplica su propia política de reintentos ni sus cabeceras por defecto — útil
    para tests o para configuración avanzada del transporte.

    Los errores de red y HTTP se traducen a la jerarquía
    :class:`~ine.errors.INEError` (ver :mod:`ine.errors`).
    """

    def __init__(
        self,
        *,
        lang: Lang = Lang.ES,
        base_url: str = "https://servicios.ine.es",
        timeout: float = 10.0,
        follow_redirects: bool = True,
        headers: Mapping[str, str] | None = None,
        retries: int = 3,
        httpx_client: httpx.Client | None = None,
        cache: Cache | None = None,
    ) -> None:
        """Construye el cliente.

        Args:
            lang: Idioma de las respuestas (``Lang.ES`` por defecto).
            base_url: Base del servicio Tempus del INE.
            timeout: Timeout por petición, en segundos.
            follow_redirects: Si seguir redirecciones HTTP.
            headers: Cabeceras extra añadidas a cada petición.
            retries: Nº máx. de reintentos sobre GET idempotente (errores de
                red + 429 + 5xx). ``0`` los desactiva. Sólo aplica cuando el
                Backend crea su propio cliente; un ``httpx_client`` inyectado se
                respeta sin modificar.
            httpx_client: Cliente HTTP inyectado (DI). Si se pasa, se reutiliza
                tal cual (sin reintentos ni cabeceras propias).
            cache: Cache en memoria opt-in (:class:`~ine._cache.Cache`). Si se
                pasa, los éxitos se cachean por ``(path, params)`` durante su
                ``ttl``; los errores no se cachean. ``None`` (default) = sin
                cache (comportamiento actual).

        Note:
            Todos los parámetros son *keyword-only*.
        """
        self._config = Config(
            lang=lang,
            base_url=base_url,
            timeout=timeout,
            follow_redirects=follow_redirects,
            headers=headers or {},
            retries=retries,
        )
        self._backend = Backend(self._config, httpx_client=httpx_client, cache=cache)
        # Servicios por dominio: cada uno encapsula un grupo de endpoints.
        self.operaciones = OperacionesService(self._backend, self._config)
        self.series = SeriesService(self._backend, self._config)
        self.datos = DatosService(self._backend, self._config)
        self.tablas = TablasService(self._backend, self._config)
        self.maestros = MaestrosService(self._backend, self._config)
        self.publicaciones = PublicacionesService(self._backend, self._config)
        self.variables = VariablesService(self._backend, self._config)

    # --- context manager ---
    def __enter__(self) -> Client:
        """Entra en el bloque ``with`` y devuelve ``self``."""
        return self

    def __exit__(self, *exc: object) -> None:
        """Sale del bloque ``with`` y cierra la conexión HTTP."""
        self.close()

    def close(self) -> None:
        """Cierra la conexión HTTP subyacente (idempotente)."""
        self._backend.close()

    # --- ficheros (CSV / PC-Axis / XLSX) ---
    def download_table(
        self,
        table_id: str,
        fmt: Format = Format.CSV_BDSC,
        *,
        path: str | Path | None = None,
        lang: str | None = None,
    ) -> Path | bytes:
        """Descarga el fichero oficial de una tabla (CSV / PC-Axis / XLSX).

        Servicio de ficheros del INE — host distinto a la API Tempus JSON:
        ``https://www.ine.es/jaxiT3/files/t/{lang}/{fmt}/{table_id}.{ext}?nocab=1``.
        Útil para tablas muy grandes que la API JSON rechaza por "restricciones
        de volumen" (p. ej. el Padrón, id 68535) o cuando se necesita el formato
        oficial. La descarga es por *streaming* (no se carga entera en memoria
        salvo que se pida explícitamente).

        Args:
            table_id: Identificador Tempus3 de la tabla (``Id``).
            fmt: Formato del fichero (:class:`Format`). Por defecto CSV (BDSC).
            path: Si se da (``str`` o :class:`~pathlib.Path`), streama por chunks
                al fichero y devuelve :class:`~pathlib.Path` — seguro para tablas
                de decenas de MB. Si es ``None`` (default), devuelve ``bytes`` en
                memoria (cuidado con tablas muy grandes).
            lang: Idioma del fichero; si es ``None`` usa el ``lang`` del cliente.

        Returns:
            :class:`~pathlib.Path` si se pasó ``path``; ``bytes`` en caso
            contrario. (No existe ``raw`` aquí: nunca se devuelven modelos.)

        Raises:
            INENotFoundError: La tabla no existe (HTTP 404).
            INEHTTPError: Otro error HTTP 4xx/5xx del servicio de ficheros.
            INEConnectionError: Error de red durante la descarga.
        """
        url = build_file_url(lang or self._config.lang.value, fmt, table_id)
        if path is not None:
            with open(path, "wb") as f, self._backend.stream(url) as response:
                for chunk in response.iter_bytes():
                    f.write(chunk)
            return Path(path)
        with self._backend.stream(url) as response:
            return response.read()
