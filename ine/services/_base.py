# ine/services/_base.py
"""Clases base para los servicios por dominio.

Cada servicio encapsula un grupo de endpoints relacionados (operaciones, series,
datos, tablas). Reciben el :class:`~ine._backend.Backend` (o ``AsyncBackend``)
y la :class:`~ine._config.Config` ya construidos por el ``Client``/``AsyncClient``,
y exponen ``self._lang`` como atajo al idioma configurado.
"""

from __future__ import annotations

from ine._backend import AsyncBackend, Backend
from ine._config import Config


class BaseService:
    """Base síncrona: guarda ``backend`` + ``config`` y expone ``_lang``."""

    def __init__(self, backend: Backend, config: Config) -> None:
        self._backend = backend
        self._config = config

    @property
    def _lang(self) -> str:
        """Idioma configurado (``config.lang.value``) como atajo para los paths."""
        return self._config.lang.value


class AsyncBaseService:
    """Base asíncrona: espejo de :class:`BaseService` con un ``AsyncBackend``."""

    def __init__(self, backend: AsyncBackend, config: Config) -> None:
        self._backend = backend
        self._config = config

    @property
    def _lang(self) -> str:
        """Idioma configurado (``config.lang.value``) como atajo para los paths."""
        return self._config.lang.value
