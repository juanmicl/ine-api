# Descarga de ficheros (CSV/PX/XLSX) para ine-api

**Fecha:** 2026-07-09  ·  **Estado:** aprobado → implementación

## Objetivo

Permitir descargar los ficheros oficiales del INE (CSV, PC-Axis, XLSX) para una tabla, especialmente para **tablas enormes que la API JSON rechaza por "restricciones de volumen"** (p. ej. el Padrón, id 68535) y para quienes necesita los formatos oficiales.

## Contexto (verificado empíricamente)

- Servicio de ficheros: `https://www.ine.es/jaxiT3/files/t/{lang}/{formato}/{id}.{ext}?nocab=1` — **host distinto** al de Tempus JSON (`servicios.ine.es/wstempus/js`).
- Formatos y content-types: `csv_bdsc`/`csv_bd` → `text/plain; ISO-8859-15`; `px` → `application/pc-axis`; `xlsx` → `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.
- **Tamaños grandes**: la tabla 68535 (Padrón) pesa ~34–70 MB según formato → **streaming obligatorio**.
- Encoding inconsistente: el INE declara `ISO-8859-15` pero los CSV llevan BOM UTF-8. Separador `;`.
- `?nocab=1` fuerza generación fresca (presente en todos los ejemplos oficiales).
- Para tablas normales, `get_datos_tabla` ya da los datos (filtrables, tipados); el fichero es **complementario**, no redundante.

## Decisiones (acordadas)

- **API pública:** método en `Client`/`AsyncClient` — `download_table(table_id, fmt=Format.CSV_BDSC, *, path=None, lang=None)`.
- **Return:** si `path` se da → **streama por chunks al fichero** y devuelve `pathlib.Path` (seguro para 70 MB); si `path=None` → devuelve `bytes` en memoria (docstring avisa del riesgo con tablas grandes).
- Reutiliza el `httpx_client` del cliente (URL absoluta → ignora el `base_url` de Tempus) → hereda reintentos/transporte.

## Arquitectura

### `ine/_files.py` (interno)
- `Format(StrEnum)`: `CSV_BDSC = "csv_bdsc"`, `CSV_BD = "csv_bd"`, `PX = "px"`, `XLSX = "xlsx"`.
- `_FILE_BASE = "https://www.ine.es/jaxiT3/files"`.
- `build_file_url(lang: str, fmt: Format, table_id: str) -> str` → `{base}/t/{lang}/{fmt}/{table_id}.{ext}?nocab=1`, donde `ext` se deriva del formato (`csv` para los csv_*, `px`, `xlsx`).
- Reexportar `Format` desde `ine` (`from ine import Format`).

### `Backend` / `AsyncBackend` — nuevo `stream()`
- `Backend.stream(url, *, params=None) -> Iterator[httpx.Response]` como `@contextmanager`: abre `self._client.stream("GET", url, params=params)`, ejecuta `self._raise_for_status(response)` (status check **antes** de ceder el body) y hace `yield response`. El caller itera `response.iter_bytes()`.
- `AsyncBackend.stream` análogo: `@asynccontextmanager` que `yield` la response; caller usa `async with ... as r: async for chunk in r.aiter_bytes()`.
- **Sin** checks H1/`_guard_json`/str-check: los ficheros no son JSON Tempus. Solo `_raise_for_status` (404→`INENotFoundError`, 5xx→`INEHTTPError`); errores de red → `INEConnectionError`.

### `Client` / `AsyncClient` — `download_table`
```
download_table(table_id, fmt=Format.CSV_BDSC, *, path=None, lang=None) -> Path | bytes
```
- `lang` = `lang or self._config.lang.value`.
- `url = build_file_url(lang, fmt, table_id)`.
- Si `path` (str | Path): `with self._backend.stream(url) as r: with open(path, "wb") as f: for chunk in r.iter_bytes(): f.write(chunk)` → devuelve `Path(path)`.
- Si `path is None`: `with self._backend.stream(url) as r: return r.read()` (bytes).
- Async: `async with` + `aiter_bytes()` / `await r.aread()`.

## Bonus: `INEVolumeError`

Cuando la API JSON responde `200` con un objeto `{"status": "..."}` (p. ej. `"No puede mostrarse por restricciones de volumen"`), hoy nuestro `get_list` lanza `INEParseError` (esperaba lista, llegó dict). Mejora:
- `errors.py`: `class INEVolumeError(INELogicalError)` — subclase (un `except INELogicalError` la sigue capturando).
- `_request` (sync+async): tras `data = response.json()`, antes del chequeo de str, si `isinstance(data, dict) and "status" in data`: `raise INEVolumeError(data["status"])` con un mensaje que sugiera usar `download_table` para tablas grandes.
- Test: un `get_datos_tabla` mocked con `{"status": "No puede mostrarse por restricciones de volumen"}` → `INEVolumeError`.

## Tests

- `_files`: mapping formato→URL (cada `Format` produce el segmento y la extensión correctos; `lang` embebido; `?nocab=1` presente).
- `stream` (Backend): 200 → cede response iterable; 404 → `INENotFoundError` (sin ceder body).
- `download_table`: path → fichero escrito por chunks, contenido correcto, devuelve `Path`; `path=None` → `bytes` iguales; formato/lang correctos en la URL; 404 → `INENotFoundError`.
- sync + async (`@pytest.mark.anyio`).
- `INEVolumeError`: el dict de volumen → `INEVolumeError` (no `INEParseError`); sigue siendo capturable por `except INELogicalError`.
- `from ine import Format` funciona.

## Dependencias

Ninguna nueva.

## Fuera de alcance (YAGNI)

- Helpers de decodificación de texto / parsing de CSV a DataFrame (el usuario decodifica los bytes como quiera).
- Detección/progresión de descarga (barra de progreso).
- Reanudación de descargas (HTTP Range) — los ficheros se regeneran; además el INE parece ignorar Range.
- Cache de ficheros (distinto del cache de la API JSON).
