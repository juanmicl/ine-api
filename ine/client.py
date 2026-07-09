# ine/client.py
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from ine._backend import Backend
from ine._cache import Cache
from ine._config import Config
from ine._config import Lang as Lang
from ine._filters import Grupo, compilar_filtros
from ine._urls import (
    build_params,
    datos_metadataoperacion_path,
    datos_serie_path,
    operacion_path,
    serie_metadataoperacion_path,
    serie_path,
    series_operacion_path,
    series_tabla_path,
    valores_serie_path,
)
from ine.models.datos import DatosSerie
from ine.models.operaciones import Operacion
from ine.models.series import Serie, Valor


class Client:
    """Cliente sincrono para la API Tempus del INE.

    Punto de entrada de la librería. Todos los parámetros del constructor son
    *keyword-only* para favorecer la estabilidad de la firma entre versiones.

    Uso típico como gestor de contexto (cierra la conexión HTTP al salir)::

        with Client() as c:
            ops = c.get_operaciones()

    También admite uso manual con :meth:`close`::

        c = Client()
        try:
            ops = c.get_operaciones()
        finally:
            c.close()

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

    # --- endpoints (compatibles con la API actual) ---
    def get_operaciones(self, *, raw: bool = False) -> list[Operacion] | list[dict[str, Any]]:
        """Lista las operaciones estadísticas disponibles.

        Recurso ``OPERACIONES_DISPONIBLES``: catálogo de operaciones (p. ej.
        IPC, EPA) sobre las que después se pueden pedir series, tablas y datos.

        Args:
            raw: Si ``True``, devuelve ``list[dict]`` con los datos crudos del
                INE sin validar contra
                :class:`~ine.models.operaciones.Operacion`.

        Returns:
            ``list[Operacion]`` por defecto, o ``list[dict]`` si ``raw=True``.

        Raises:
            INEConnectionError: Error de red (timeout, DNS, reset de conexión).
            INENotFoundError: Recurso no encontrado (HTTP 404).
            INELogicalError: La API respondió 200 con un mensaje de error lógico.
            INEParseError: La respuesta no es JSON o no tiene la forma esperada.
            INEHTTPError: Otro error HTTP 4xx/5xx.
        """
        data = self._backend.get_list(
            f"/wstempus/js/{self._config.lang.value}/OPERACIONES_DISPONIBLES"
        )
        if raw:
            return data
        return [Operacion.model_validate(d) for d in data]

    def get_tablas(self, operacion: str) -> list[dict[str, Any]]:
        """Lista las tablas de una operación.

        Recurso ``TABLAS_OPERACION/{operacion}``: tablas (vistas predefinidas)
        en las que se publica la operación indicada. El INE no documenta un
        esquema estable para este recurso, por lo que se devuelve siempre como
        ``list[dict]`` crudo (sin modelo).

        Args:
            operacion: Identificador de la operación: ``Id`` o ``Codigo``
                Tempus3, o el código ``IOEXXXX`` del INE.

        Returns:
            Las tablas de la operación como ``list[dict]`` (sin modelo).

        Raises:
            INEConnectionError: Error de red (timeout, DNS, reset de conexión).
            INENotFoundError: Recurso no encontrado (HTTP 404).
            INELogicalError: La API respondió 200 con un mensaje de error lógico.
            INEParseError: La respuesta no es JSON o no tiene la forma esperada.
            INEHTTPError: Otro error HTTP 4xx/5xx.
        """
        return self._backend.get_list(
            f"/wstempus/js/{self._config.lang.value}/TABLAS_OPERACION/{operacion}"
        )

    def get_datos_tabla(
        self, tabla_id: str, *, raw: bool = False
    ) -> list[DatosSerie] | list[dict[str, Any]]:
        """Devuelve los datos de una tabla.

        Recurso ``DATOS_TABLA/{tabla_id}``: observaciones de las series que
        componen la tabla indicada.

        Args:
            tabla_id: Identificador Tempus3 de la tabla (``Id``).
            raw: Si ``True``, devuelve ``list[dict]`` con los datos crudos del
                INE sin validar contra :class:`~ine.models.datos.DatosSerie`.

        Returns:
            ``list[DatosSerie]`` por defecto, o ``list[dict]`` si ``raw=True``.

        Raises:
            INEConnectionError: Error de red (timeout, DNS, reset de conexión).
            INENotFoundError: Recurso no encontrado (HTTP 404).
            INELogicalError: La API respondió 200 con un mensaje de error lógico.
            INEParseError: La respuesta no es JSON o no tiene la forma esperada.
            INEHTTPError: Otro error HTTP 4xx/5xx.
        """
        data = self._backend.get_list(
            f"/wstempus/js/{self._config.lang.value}/DATOS_TABLA/{tabla_id}"
        )
        if raw:
            return data
        return [DatosSerie.model_validate(d) for d in data]

    # --- OPERACION / DATOS (Fase 5) ---
    def get_operacion(
        self, id: str, *, det: str | None = None, raw: bool = False
    ) -> list[Operacion] | list[dict[str, Any]]:
        """Devuelve los metadatos de una operación.

        Recurso ``OPERACION/{id}``: ficha de la operación (nombre, código,
        IOE...). El INE entrega siempre una lista (habitualmente de un elemento).

        Args:
            id: Identificador de la operación: ``Id``, ``Codigo`` o ``IOEXXXX``.
            det: Nivel de detalle: ``"0"`` básico, ``"1"`` detallado,
                ``"2"`` muy detallado.
            raw: Si ``True``, devuelve ``list[dict]`` con los datos crudos del
                INE sin validar contra
                :class:`~ine.models.operaciones.Operacion`.

        Returns:
            ``list[Operacion]`` por defecto, o ``list[dict]`` si ``raw=True``.

        Raises:
            INEConnectionError: Error de red (timeout, DNS, reset de conexión).
            INENotFoundError: Recurso no encontrado (HTTP 404).
            INELogicalError: La API respondió 200 con un mensaje de error lógico.
            INEParseError: La respuesta no es JSON o no tiene la forma esperada.
            INEHTTPError: Otro error HTTP 4xx/5xx.
        """
        data = self._backend.get_list(
            operacion_path(self._config.lang.value, id),
            build_params(det=det),
        )
        if raw:
            return data
        return [Operacion.model_validate(d) for d in data]

    def get_datos_serie(
        self,
        id_serie: str,
        *,
        nult: int | None = None,
        det: str | None = None,
        tip: str | None = None,
        date: list[str] | None = None,
        raw: bool = False,
    ) -> list[DatosSerie] | list[dict[str, Any]]:
        """Devuelve las observaciones (datos) de una serie.

        Recurso ``DATOS_SERIE/{id_serie}``: valores temporales de la serie, con
        filtros opcionales de detalle, tipo, últimos periodos y rango de fechas.

        Args:
            id_serie: Identificador Tempus3 de la serie (``Id``).
            nult: Devuelve los ``nult`` últimos datos o periodos de la serie.
            det: Nivel de detalle: ``"0"`` básico, ``"1"`` detallado,
                ``"2"`` muy detallado.
            tip: Tipo de respuesta: ``"A"`` amigable, ``"M"`` con metadatos,
                ``"AM"`` ambos.
            date: Rango ``aaaammdd:aaaammdd``; si se omite el final
                (``aaaammdd:``) se usa hasta el fin de la serie.
            raw: Si ``True``, devuelve ``list[dict]`` con los datos crudos del
                INE sin validar contra :class:`~ine.models.datos.DatosSerie`.

        Returns:
            ``list[DatosSerie]`` por defecto, o ``list[dict]`` si ``raw=True``.

        Raises:
            INEConnectionError: Error de red (timeout, DNS, reset de conexión).
            INENotFoundError: Recurso no encontrado (HTTP 404).
            INELogicalError: La API respondió 200 con un mensaje de error lógico.
            INEParseError: La respuesta no es JSON o no tiene la forma esperada.
            INEHTTPError: Otro error HTTP 4xx/5xx.
        """
        data = self._backend.get_list(
            datos_serie_path(self._config.lang.value, id_serie),
            build_params(nult=nult, det=det, tip=tip, date=date),
        )
        if raw:
            return data
        return [DatosSerie.model_validate(d) for d in data]

    def get_datos_metadataoperacion(
        self,
        op: str,
        *,
        p: str | None = None,
        nult: int | None = None,
        det: str | None = None,
        tip: str | None = None,
        filtros: list[Grupo] | None = None,
        raw: bool = False,
    ) -> list[DatosSerie] | list[dict[str, Any]]:
        """Devuelve los datos de una operación por metadatos (con filtros ``g``).

        Recurso ``DATOS_METADATAOPERACION/{op}``: observaciones de la operación
        permitiendo filtrar por periodicidad, últimos periodos y combinaciones
        OR/AND de variables mediante :data:`~ine._filters.Grupo`.

        Args:
            op: Identificador de la operación: ``Id``, ``Codigo`` o ``IOEXXXX``.
            p: Periodicidad: ``"1"`` mensual, ``"3"`` trimestral, ``"6"``
                bianual, ``"12"`` anual.
            nult: Devuelve los ``nult`` últimos datos o periodos de la serie.
            det: Nivel de detalle: ``"0"`` básico, ``"1"`` detallado,
                ``"2"`` muy detallado.
            tip: Tipo de respuesta: ``"A"`` amigable, ``"M"`` con metadatos,
                ``"AM"`` ambos.
            filtros: Filtros OR/AND: varias condiciones en un mismo
                :data:`~ine._filters.Grupo` = OR; grupos distintos = AND. Se
                compilan al parámetro ``g`` del INE.
            raw: Si ``True``, devuelve ``list[dict]`` con los datos crudos del
                INE sin validar contra :class:`~ine.models.datos.DatosSerie`.

        Returns:
            ``list[DatosSerie]`` por defecto, o ``list[dict]`` si ``raw=True``.

        Raises:
            INEConnectionError: Error de red (timeout, DNS, reset de conexión).
            INENotFoundError: Recurso no encontrado (HTTP 404).
            INELogicalError: La API respondió 200 con un mensaje de error lógico.
            INEParseError: La respuesta no es JSON o no tiene la forma esperada.
            INEHTTPError: Otro error HTTP 4xx/5xx.
        """
        params = build_params(p=p, nult=nult, det=det, tip=tip)
        if filtros is not None:
            params |= compilar_filtros(filtros)
        data = self._backend.get_list(
            datos_metadataoperacion_path(self._config.lang.value, op),
            params,
        )
        if raw:
            return data
        return [DatosSerie.model_validate(d) for d in data]

    # --- SERIES (Fase 5) ---
    def get_serie(
        self,
        id_serie: str,
        *,
        det: str | None = None,
        tip: str | None = None,
        raw: bool = False,
    ) -> list[Serie] | list[dict[str, Any]]:
        """Devuelve los metadatos de una serie.

        Recurso ``SERIE/{id_serie}``: ficha de la serie (código, nombre,
        decimales, operación, periodicidad...). El INE entrega siempre una lista.

        Args:
            id_serie: Identificador Tempus3 de la serie (``Id``).
            det: Nivel de detalle: ``"0"`` básico, ``"1"`` detallado,
                ``"2"`` muy detallado.
            tip: Tipo de respuesta: ``"A"`` amigable, ``"M"`` con metadatos,
                ``"AM"`` ambos.
            raw: Si ``True``, devuelve ``list[dict]`` con los datos crudos del
                INE sin validar contra :class:`~ine.models.series.Serie`.

        Returns:
            ``list[Serie]`` por defecto, o ``list[dict]`` si ``raw=True``.

        Raises:
            INEConnectionError: Error de red (timeout, DNS, reset de conexión).
            INENotFoundError: Recurso no encontrado (HTTP 404).
            INELogicalError: La API respondió 200 con un mensaje de error lógico.
            INEParseError: La respuesta no es JSON o no tiene la forma esperada.
            INEHTTPError: Otro error HTTP 4xx/5xx.
        """
        data = self._backend.get_list(
            serie_path(self._config.lang.value, id_serie),
            build_params(det=det, tip=tip),
        )
        if raw:
            return data
        return [Serie.model_validate(d) for d in data]

    def get_series_operacion(
        self,
        op: str,
        *,
        det: str | None = None,
        tip: str | None = None,
        page: int | None = None,
        raw: bool = False,
    ) -> list[Serie] | list[dict[str, Any]]:
        """Lista las series de una operación.

        Recurso ``SERIES_OPERACION/{op}``: catálogo de series publicadas bajo
        la operación indicada, paginado (hasta 500 elementos por página).

        Args:
            op: Identificador de la operación: ``Id``, ``Codigo`` o ``IOEXXXX``.
            det: Nivel de detalle: ``"0"`` básico, ``"1"`` detallado,
                ``"2"`` muy detallado.
            tip: Tipo de respuesta: ``"A"`` amigable, ``"M"`` con metadatos,
                ``"AM"`` ambos.
            page: Número de página (el INE devuelve hasta 500 elementos por
                página).
            raw: Si ``True``, devuelve ``list[dict]`` con los datos crudos del
                INE sin validar contra :class:`~ine.models.series.Serie`.

        Returns:
            ``list[Serie]`` por defecto, o ``list[dict]`` si ``raw=True``.

        Raises:
            INEConnectionError: Error de red (timeout, DNS, reset de conexión).
            INENotFoundError: Recurso no encontrado (HTTP 404).
            INELogicalError: La API respondió 200 con un mensaje de error lógico.
            INEParseError: La respuesta no es JSON o no tiene la forma esperada.
            INEHTTPError: Otro error HTTP 4xx/5xx.
        """
        data = self._backend.get_list(
            series_operacion_path(self._config.lang.value, op),
            build_params(det=det, tip=tip, page=page),
        )
        if raw:
            return data
        return [Serie.model_validate(d) for d in data]

    def get_series_tabla(
        self,
        id_tabla: str,
        *,
        det: str | None = None,
        tip: str | None = None,
        tv: list[str] | None = None,
        raw: bool = False,
    ) -> list[Serie] | list[dict[str, Any]]:
        """Lista las series que componen una tabla.

        Recurso ``SERIES_TABLA/{id_tabla}``: series individuales incluidas en la
        tabla indicada, con filtros opcionales por variable/valor.

        Args:
            id_tabla: Identificador Tempus3 de la tabla (``Id``).
            det: Nivel de detalle: ``"0"`` básico, ``"1"`` detallado,
                ``"2"`` muy detallado.
            tip: Tipo de respuesta: ``"A"`` amigable, ``"M"`` con metadatos,
                ``"AM"`` ambos.
            tv: Filtros ``id_variable:id_valor`` (repetibles).
            raw: Si ``True``, devuelve ``list[dict]`` con los datos crudos del
                INE sin validar contra :class:`~ine.models.series.Serie`.

        Returns:
            ``list[Serie]`` por defecto, o ``list[dict]`` si ``raw=True``.

        Raises:
            INEConnectionError: Error de red (timeout, DNS, reset de conexión).
            INENotFoundError: Recurso no encontrado (HTTP 404).
            INELogicalError: La API respondió 200 con un mensaje de error lógico.
            INEParseError: La respuesta no es JSON o no tiene la forma esperada.
            INEHTTPError: Otro error HTTP 4xx/5xx.
        """
        data = self._backend.get_list(
            series_tabla_path(self._config.lang.value, id_tabla),
            build_params(det=det, tip=tip, tv=tv),
        )
        if raw:
            return data
        return [Serie.model_validate(d) for d in data]

    def get_valores_serie(
        self, id_serie: str, *, det: str | None = None, raw: bool = False
    ) -> list[Valor] | list[dict[str, Any]]:
        """Devuelve los valores de las variables de una serie.

        Recurso ``VALORES_SERIE/{id_serie}``: para cada variable que define la
        serie, los valores (categorías) que toma. Útil para construir los
        filtros ``tv`` / ``g`` de otras llamadas.

        Args:
            id_serie: Identificador Tempus3 de la serie (``Id``).
            det: Nivel de detalle: ``"0"`` básico, ``"1"`` detallado,
                ``"2"`` muy detallado.
            raw: Si ``True``, devuelve ``list[dict]`` con los datos crudos del
                INE sin validar contra :class:`~ine.models.series.Valor`.

        Returns:
            ``list[Valor]`` por defecto, o ``list[dict]`` si ``raw=True``.

        Raises:
            INEConnectionError: Error de red (timeout, DNS, reset de conexión).
            INENotFoundError: Recurso no encontrado (HTTP 404).
            INELogicalError: La API respondió 200 con un mensaje de error lógico.
            INEParseError: La respuesta no es JSON o no tiene la forma esperada.
            INEHTTPError: Otro error HTTP 4xx/5xx.
        """
        data = self._backend.get_list(
            valores_serie_path(self._config.lang.value, id_serie),
            build_params(det=det),
        )
        if raw:
            return data
        return [Valor.model_validate(d) for d in data]

    def get_series_metadata_operacion(
        self,
        op: str,
        *,
        p: str | None = None,
        det: str | None = None,
        tip: str | None = None,
        filtros: list[Grupo] | None = None,
        raw: bool = False,
    ) -> list[Serie] | list[dict[str, Any]]:
        """Devuelve las series de una operación por metadatos (con filtros ``g``).

        Recurso ``SERIE_METADATAOPERACION/{op}``: catálogo de series de la
        operación permitiendo filtrar por periodicidad y combinaciones OR/AND de
        variables mediante :data:`~ine._filters.Grupo`.

        Args:
            op: Identificador de la operación: ``Id``, ``Codigo`` o ``IOEXXXX``.
            p: Periodicidad: ``"1"`` mensual, ``"3"`` trimestral, ``"6"``
                bianual, ``"12"`` anual.
            det: Nivel de detalle: ``"0"`` básico, ``"1"`` detallado,
                ``"2"`` muy detallado.
            tip: Tipo de respuesta: ``"A"`` amigable, ``"M"`` con metadatos,
                ``"AM"`` ambos.
            filtros: Filtros OR/AND: varias condiciones en un mismo
                :data:`~ine._filters.Grupo` = OR; grupos distintos = AND. Se
                compilan al parámetro ``g`` del INE.
            raw: Si ``True``, devuelve ``list[dict]`` con los datos crudos del
                INE sin validar contra :class:`~ine.models.series.Serie`.

        Returns:
            ``list[Serie]`` por defecto, o ``list[dict]`` si ``raw=True``.

        Raises:
            INEConnectionError: Error de red (timeout, DNS, reset de conexión).
            INENotFoundError: Recurso no encontrado (HTTP 404).
            INELogicalError: La API respondió 200 con un mensaje de error lógico.
            INEParseError: La respuesta no es JSON o no tiene la forma esperada.
            INEHTTPError: Otro error HTTP 4xx/5xx.
        """
        params = build_params(p=p, det=det, tip=tip)
        if filtros is not None:
            params |= compilar_filtros(filtros)
        data = self._backend.get_list(
            serie_metadataoperacion_path(self._config.lang.value, op),
            params,
        )
        if raw:
            return data
        return [Serie.model_validate(d) for d in data]
