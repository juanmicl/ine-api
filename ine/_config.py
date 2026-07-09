from __future__ import annotations

import importlib.metadata
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

try:
    __version__ = importlib.metadata.version("ine-api")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"


class Lang(StrEnum):
    """Idiomas admitidos por la API Tempus del INE.

    Determina el segmento ``/js/{lang}/`` de las URLs y, por tanto, el idioma
    de los textos (nombres de operaciones, series, valores...) de la respuesta.
    """

    ES = "ES"
    EN = "EN"
    CA = "CA"
    GL = "GL"
    EU = "EU"


_USER_AGENT = f"ine-api/{__version__}"


@dataclass(frozen=True)
class Config:
    """Configuración inmutable del cliente (transporte, timeouts, reintentos).

    La construye internamente :class:`~ine.client.Client` /
    :class:`~ine.async_client.AsyncClient` a partir de sus parámetros
    *keyword-only*; los usuarios rara vez la instancian directamente.
    """

    lang: Lang = Lang.ES
    base_url: str = "https://servicios.ine.es"
    timeout: float = 10.0
    follow_redirects: bool = True
    user_agent: str = _USER_AGENT
    headers: Mapping[str, str] = field(default_factory=dict)
    # Nº máx. de reintentos sobre GET idempotente (errores de red + 429 + 5xx).
    # 0 desactiva los reintentos. Sólo aplica cuando el Backend construye su
    # propio httpx.Client; un cliente inyectado (DI) se respetaría tal cual.
    retries: int = 3
