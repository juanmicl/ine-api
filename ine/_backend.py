# ine/_backend.py
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from ine._config import Config
from ine.errors import (
    INEConnectionError,
    INEHTTPError,
    INELogicalError,
    INENotFoundError,
    INEParseError,
)


class Backend:
    """Costura I/O sincrona. Único punto que sabe de httpx."""

    def __init__(self, config: Config, httpx_client: httpx.Client | None = None) -> None:
        self._config = config
        if httpx_client is None:
            httpx_client = httpx.Client(
                base_url=config.base_url,
                timeout=config.timeout,
                follow_redirects=config.follow_redirects,
                headers={"User-Agent": config.user_agent, **dict(config.headers)},
            )
        self._client = httpx_client

    def get(self, path: str, params: Mapping[str, Any] | None = None) -> list[Any] | dict[Any, Any]:
        try:
            response = self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            raise INEConnectionError(str(exc)) from exc
        self._raise_for_status(response)
        self._guard_json(response)
        # La API devuelve list/dict en éxito, o str (mensaje de error lógico, H1).
        data: list[Any] | dict[Any, Any] | str = response.json()
        if isinstance(data, str):
            raise INELogicalError(data)
        return data

    def close(self) -> None:
        self._client.close()

    @staticmethod
    def _guard_json(response: httpx.Response) -> None:
        ctype = response.headers.get("content-type", "")
        if "application/json" not in ctype:
            raise INEParseError(
                f"Respuesta no JSON (content-type={ctype!r}): {response.text[:200]}"
            )

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.is_success:
            return
        url = str(response.request.url)
        body = response.text
        if response.status_code == 404:
            raise INENotFoundError(status=404, url=url, body=body)
        raise INEHTTPError(status=response.status_code, url=url, body=body)
