# ine/client.py
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from ine._backend import Backend
from ine._config import Config
from ine._config import Lang as Lang
from ine._filters import Grupo, compilar_filtros
from ine._urls import (
    build_params,
    datos_metadataoperacion_path,
    datos_serie_path,
    operacion_path,
)
from ine.models.datos import DatosSerie
from ine.models.operaciones import Operacion


class Client:
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
    ) -> None:
        self._config = Config(
            lang=lang,
            base_url=base_url,
            timeout=timeout,
            follow_redirects=follow_redirects,
            headers=headers or {},
            retries=retries,
        )
        self._backend = Backend(self._config, httpx_client=httpx_client)

    # --- context manager ---
    def __enter__(self) -> Client:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._backend.close()

    # --- endpoints (compatibles con la API actual) ---
    def get_operaciones(self, *, raw: bool = False) -> list[Operacion] | list[dict[str, Any]]:
        data = self._backend.get_list(
            f"/wstempus/js/{self._config.lang.value}/OPERACIONES_DISPONIBLES"
        )
        if raw:
            return data
        return [Operacion.model_validate(d) for d in data]

    def get_tablas(self, operacion: str) -> list[dict[str, Any]]:
        return self._backend.get_list(
            f"/wstempus/js/{self._config.lang.value}/TABLAS_OPERACION/{operacion}"
        )

    def get_datos_tabla(
        self, tabla_id: str, *, raw: bool = False
    ) -> list[DatosSerie] | list[dict[str, Any]]:
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
