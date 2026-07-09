# ine/client.py
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from ine._backend import Backend
from ine._config import Config
from ine._config import Lang as Lang


class Client:
    def __init__(
        self,
        *,
        lang: Lang = Lang.ES,
        base_url: str = "https://servicios.ine.es",
        timeout: float = 10.0,
        follow_redirects: bool = True,
        headers: Mapping[str, str] | None = None,
        httpx_client: httpx.Client | None = None,
    ) -> None:
        self._config = Config(
            lang=lang,
            base_url=base_url,
            timeout=timeout,
            follow_redirects=follow_redirects,
            headers=headers or {},
        )
        self._backend = Backend(self._config, httpx_client=httpx_client)

    # --- context manager ---
    def __enter__(self) -> Client:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._backend.close()

    # --- endpoints (compatibles con la API actual; aún devuelven list) ---
    def get_operaciones(self) -> list[dict[str, Any]]:
        return self._backend.get_list(
            f"/wstempus/js/{self._config.lang.value}/OPERACIONES_DISPONIBLES"
        )

    def get_tablas(self, operacion: str) -> list[dict[str, Any]]:
        return self._backend.get_list(
            f"/wstempus/js/{self._config.lang.value}/TABLAS_OPERACION/{operacion}"
        )

    def get_datos_tabla(self, tabla_id: str) -> list[dict[str, Any]]:
        return self._backend.get_list(
            f"/wstempus/js/{self._config.lang.value}/DATOS_TABLA/{tabla_id}"
        )
