# ine/errors.py
from __future__ import annotations


class INEError(Exception):
    """Raíz de todas las excepciones del cliente ine."""


class INEConnectionError(INEError):
    """Problemas de red: timeout, DNS, reset de conexión."""


class INEHTTPError(INEError):
    """Respuesta HTTP de error (4xx/5xx) traducida desde httpx."""

    def __init__(self, *, status: int, url: str, body: str) -> None:
        self.status = status
        self.url = url
        self.body = body
        super().__init__(f"HTTP {status} en {url}: {body[:200]}")


class INENotFoundError(INEHTTPError):
    """Recurso no encontrado (404)."""


class INEParseError(INEError):
    """La respuesta no es JSON o no tiene la forma esperada."""


class INELogicalError(INEError):
    """La API devolvió 200 pero con un mensaje de error lógico (H1)."""
