# Cache en memoria opt-in para `ine-api`

**Fecha:** 2026-07-09  ·  **Estado:** aprobado → implementación

## Objetivo

Evitar repetir peticiones idénticas al INE dentro de un mismo proceso (no "reventarle la API"), reduciendo latencia y carga, **sin sorprender al usuario con datos stale por defecto**.

## Decisiones (acordadas en brainstorming)

1. **Alcance:** memoria por proceso (no persistente). Se pierde al cerrar el proceso.
2. **Expiración:** TTL único global (configurable), aplicado a todas las peticiones GET cacheadas.
3. **Activación:** opt-in explícito vía `Client(cache=Cache(ttl=...))`. Por defecto `cache=None` = sin cache (comportamiento actual). **Nunca transparente por defecto** (evita staleness sorpresa).
4. **Sin dependencias nuevas** (store TTL propio).

## Arquitectura

### `ine/_cache.py` → clase pública `Cache`

```
Cache(*, ttl: float = 300.0, maxsize: int | None = None)
```

- Interno: `dict[key → (timestamp, data)]`.
- API: `get(key) -> data | None` (devuelve `None` si miss/expirado), `set(key, data)`, `clear()`, `__len__`, `__contains__`.
- `ttl` en segundos. `maxsize=None` (solo TTL) por defecto; si se indica, evicción cuando se alcanza (FIFO simple).
- **Sin lock**: dos awaits concurrentes sobre una clave fría pueden duplicar el fetch (aceptable; anti-stampede = YAGNI). El store es seguro de compartir entre sync y async (operaciones de dict atómicas bajo GIL / single event loop).

### Integración en `Backend` / `AsyncBackend`

- `Backend.__init__(config, httpx_client=None, cache=None)` (mismo para `AsyncBackend`).
- Nuevo método privado `_cached_request(path, params) -> list[Any] | dict[str, Any]`:
  - **Key:** `(path, json.dumps(params or {}, sort_keys=True, default=str))` — estable; `lang` ya va en `path`.
  - Si `self._cache` existe y hay hit fresco → devuelve el data cacheado.
  - Si no → `data = self._request(path, params)` (la lógica H1/H2/H3 **intacta**) → `self._cache.set(key, data)` → devuelve.
- `get_list` / `get_one` llaman a `_cached_request` en lugar de `_request` directamente.
- `_request` queda sin cambios (pureza de la costura I/O + manejo de errores).

### `Client` / `AsyncClient`

- Nuevo kwarg keyword-only `cache: Cache | None = None`, pasado al Backend. Default `None`.
- `from ine import Cache` (reexport en `ine/__init__.py`).

## Casos de borde

- **Solo se cachea el éxito:** los `INEError` (404, logical-error, connection, parse) **no** se cachean — se relanzan en cada llamada.
- **`raw=True` y modelos comparten cache:** se cachea el dict post-`_request`; el modelado pydantic se re-ejecuta sobre el hit (barato, correcto). No se cachean modelos.
- El cache es **compartible entre varios `Client`** (el usuario posee la instancia).
- `cache=None` ⇒ comportamiento idéntico al actual (cero overhead).

## Tests

- hit/miss (segunda llamada no hace HTTP).
- expiración TTL (ttl corto o mock de tiempo → expira y vuelve a hacer fetch).
- `clear()` vacía el cache.
- `cache=None` siempre hace HTTP.
- errores (`INEError`) no se cachean.
- sync + async comparten el mismo store.
- la key distingue por `params` (distintos params → entradas distintas; mismos params → hit).

## Dependencias

Ninguna nueva.

## Fuera de alcance (YAGNI)

- Cache persistente en disco (cross-run).
- TTL diferenciado por tipo (metadata vs datos).
- Anti-stampede (single-flight).
- HTTP conditional requests (ETag/If-Modified-Since).
- Cachear los modelos pydantic.
