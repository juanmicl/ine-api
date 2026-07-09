# Refactor a namespaces — ine-api

**Fecha:** 2026-07-09  ·  **Estado:** aprobado → implementación  ·  **Cambio *breaking*** (v0.x)

## Objetivo

Pasar de métodos planos (`client.get_operaciones()`) a **namespaces por dominio** (`client.operaciones.list()`), ahora que se superan los ~10 métodos (12 + `download_table`). Es un cambio *breaking* de la API pública; estamos en 0.x, es el momento.

## Mapeo (aprobado)

| Actual (plano) | Nuevo (namespace) |
|---|---|
| `get_operaciones()` | `client.operaciones.list(*, det=None, geo=None, page=None, raw=False)` |
| `get_operacion(id)` | `client.operaciones.get(id, *, det=None, raw=False)` |
| `get_serie(id)` | `client.series.get(id, *, det=None, tip=None, raw=False)` |
| `get_series_operacion(op)` | `client.series.by_operacion(op, *, det=None, tip=None, page=None, raw=False)` |
| `get_series_tabla(id)` | `client.series.by_tabla(id, *, det=None, tip=None, tv=None, raw=False)` |
| `get_valores_serie(id)` | `client.series.valores(id, *, det=None, raw=False)` |
| `get_series_metadata_operacion(op, filtros=)` | `client.series.metadata_operacion(op, *, p=None, det=None, tip=None, filtros=None, raw=False)` |
| `get_datos_tabla(id)` | `client.datos.tabla(id, *, nult=None, det=None, tip=None, tv=None, date=None, raw=False)` |
| `get_datos_serie(id)` | `client.datos.serie(id, *, nult=None, det=None, tip=None, date=None, raw=False)` |
| `get_datos_metadataoperacion(op, filtros=)` | `client.datos.metadata_operacion(op, *, p=None, nult=None, det=None, tip=None, filtros=None, raw=False)` |
| `get_tablas(op)` | `client.tablas.by_operacion(op, *, det=None, geo=None, tip=None, raw=False)` |
| `download_table(...)` | **se queda en la raíz**: `client.download_table(...)` (servicio de ficheros, distinto) |

Los parámetros y comportamientos (raw, modelos, errores) se conservan **idénticos** — solo se reubica y renombra.

## Convenciones de nombres

- `list()` — colección principal de un dominio.
- `get(id)` — un elemento por id.
- `by_operacion(op)` / `by_tabla(id)` — listas con scope.
- Verbos de dominio donde es natural: `datos.tabla`, `datos.serie`, `series.valores`.

## Estructura

```
ine/services/
  __init__.py
  _base.py        # BaseService(backend, config) + AsyncBaseService; ._lang property
  operaciones.py  # OperacionesService (sync) + AsyncOperacionesService
  series.py       # SeriesService + AsyncSeriesService
  datos.py        # DatosService + AsyncDatosService
  tablas.py       # TablasService + AsyncTablasService (get_tablas sigue raw)
```

- `BaseService.__init__(self, backend, config)` guarda `self._backend`, `self._config`; property `_lang -> self._config.lang.value`. `AsyncBaseService` igual (su `backend` es `AsyncBackend`).
- Cada método de servicio reutiliza los builders de `_urls.py`, `build_params`, los modelos y el `backend.get_list`/`get_one`. Cuerpo = el del método plano actual, reubicado.
- **`Client`/`AsyncClient`**: en `__init__` instancian los servicios:
  - sync: `self.operaciones = OperacionesService(self._backend, self._config)`, etc.
  - async: `self.operaciones = AsyncOperacionesService(self._backend, self._config)`, etc.
  - Se **eliminan** los métodos planos (`get_operaciones`, …) salvo `download_table` (raíz), `__init__`/`__enter__`/`__exit__`/`close`/`__aenter__`/`__aexit__`.
  - `download_table` no cambia (usa `self._backend.stream`).

## Actualizaciones obligatorias (parte del refactor)

- **Todos los tests** (`tests/*.py`): cada `client.get_xxx(...)` → `client.<ns>.<method>(...)`; lo mismo para `AsyncClient`. Sin cambiar aserciones ni fixtures.
- `hello.py` y `examples/*.py`: al nuevo estilo.
- `README.md`: quickstart + tabla de cobertura + sección de configuración al nuevo estilo.

## Test de no-regresión

- `uv run pytest -q` verde (mismo número que hoy, 166; solo cambian las llamadas).
- `uv run ruff check .` y `uv run mypy ine` limpios.
- `from ine import Client` y `client.operaciones.list` existen; los métodos planos ya **no** existen en `Client`.

## Fuera de alcance

- Nuevos endpoints (los dominios pendientes TABLAS/VARIABLES/VALORES/MAESTROS/PUBLICACIONES) — esto es solo reorganizar lo existente.
- Cambiar `download_table`.
