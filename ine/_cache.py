from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any


def _now() -> float:
    """Reloj monotónico (punto de indirección para tests deterministas)."""
    return time.monotonic()


class Cache:
    """Cache en memoria con expiración por TTL.

    Opt-in: el usuario la crea y la pasa a ``Client(cache=...)``. No se activa
    por defecto. Solo guarda datos válidos (la integración cachea éxitos, no
    errores). Sin lock: dos llamadas concurrentes sobre una clave fría pueden
    duplicar el fetch (aceptable; anti-stampede = YAGNI).
    """

    def __init__(self, *, ttl: float = 300.0, maxsize: int | None = None) -> None:
        if ttl < 0:
            raise ValueError("ttl debe ser >= 0")
        if maxsize is not None and maxsize <= 0:
            raise ValueError("maxsize debe ser > 0 o None")
        self._ttl = ttl
        self._maxsize = maxsize
        # key -> (expiry, data)
        self._store: OrderedDict[Any, tuple[float, Any]] = OrderedDict()

    def get(self, key: Any) -> Any | None:
        """Devuelve el valor si existe y NO ha expirado; si no, ``None`` (y lo purga si expiró)."""
        entry = self._store.get(key)
        if entry is None:
            return None
        expiry, data = entry
        if _now() >= expiry:
            del self._store[key]
            return None
        return data

    def set(self, key: Any, data: Any) -> None:
        """Guarda ``data`` bajo ``key`` con expiración = ahora + ttl."""
        if key in self._store:
            del self._store[key]  # reinsertar al final (recency / FIFO)
        self._store[key] = (_now() + self._ttl, data)
        self._evict()

    def clear(self) -> None:
        """Vacía por completo el cache."""
        self._store.clear()

    def _evict(self) -> None:
        if self._maxsize is None:
            return
        while len(self._store) > self._maxsize:
            self._store.popitem(last=False)  # evicta el más antiguo (FIFO)

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key: object) -> bool:
        return self.get(key) is not None
