# ine-api

Cliente Python tipado (sync + async) para la API Tempus del INE (Instituto Nacional de Estadística de España).

![Python](https://img.shields.io/badge/python-3.12-blue)
![Licencia](https://img.shields.io/badge/license-MIT-green)
![tipado](https://img.shields.io/badge/type--checked-py.typed-purple)

---

## Estado

**En desarrollo (SemVer 0.x).** La API pública aún puede cambiar. Este cliente
**cubre parcialmente** la API Tempus del INE (10 de los endpoints; ver
[Cobertura](#cobertura-de-endpoints)). Publicado en
[PyPI](https://pypi.org/project/ine-api/).

---

## Instalación

Requiere **Python ≥ 3.12**.

```bash
pip install ine-api
```

o con [`uv`](https://docs.astral.sh/uv/):

```bash
uv add ine-api
```

**Desarrollo / contribución:**

```bash
git clone https://github.com/juanmicl/ine-api.git
cd ine-api
uv sync          # instala runtime + dev en un .venv aislado
uv run pytest    # corre los tests
```

---

## Quickstart (sync)

```python
from ine import Client, Lang

with Client(lang=Lang.ES) as client:
    operaciones = client.operaciones.list()
    for op in operaciones[:5]:
        print(op.id, op.codigo, op.nombre)

    # Últimas 12 observaciones de la serie IPC53262.
    # Troceamos en local: en vivo, `nult` puede devolver cuerpos vacíos
    # para algunas series del INE.
    datos = client.datos.serie("53262")
    for serie in datos:
        for obs in serie.data[-12:]:
            print(obs.fecha.isoformat(), obs.valor)
```

`Client` es un gestor de contexto: cierra la conexión HTTP al salir del bloque.
Las respuestas se validan con **pydantic** (`Operacion`, `DatosSerie`, ...).

---

## Quickstart (async)

Para aplicaciones que ya usan `asyncio` (FastAPI, crawlers, etc.):

```python
import asyncio

from ine import AsyncClient, Lang


async def main() -> None:
    async with AsyncClient(lang=Lang.ES) as client:
        operaciones = await client.operaciones.list()
        for op in operaciones[:5]:
            print(op.id, op.codigo, op.nombre)

        # Últimas 12 observaciones (troceamos en local; ver nota en el quickstart sync).
        datos = await client.datos.serie("53262")
        for serie in datos:
            for obs in serie.data[-12:]:
                print(obs.fecha.isoformat(), obs.valor)


asyncio.run(main())
```

`AsyncClient` es el espejo asíncrono de `Client`: misma API, pero cada método
es una coroutine que se espera con `await`.

---

## ¿Por qué existe?

La API Tempus del INE tiene varias rarezas que un *wrapper* ingenuo no maneja
correctamente. Este cliente las traduce a excepciones tipadas y a modelos
pydantic:

1. **HTTP 200 con cuerpo de error.** El INE responde `200 OK` con el *body*
   `"La operación indicada no existe (X)"` (un *string* JSON) cuando un recurso
   lógico no existe. `raise_for_status()` no lo detecta → el cliente lo traduce
   a `INELogicalError`.
2. **Redirecciones al resolver códigos.** Al pedir por código alfanumérico (p.
   ej. `IPC`), la API hace un `301` al `Id` numérico. El cliente sigue
   redirecciones por defecto.
3. **Los 404 devuelven HTML, no JSON.** Un recurso inexistente responde `404`
   con una página HTML. El cliente lo detecta por estado y por *content-type*
   y lo traduce a `INENotFoundError` / `INEParseError`.

Además, el esquema del INE es irregular (claves PascalCase, `FK_`/`T3_`,
`Fecha` como *epoch* en ms, campos opcionales inconsistentes). Los modelos
pydantic normalizan las claves a *snake_case* y ofrecen `raw=True` como
válvula de escape cuando el esquema cambia.

---

## Manejo de errores

Todas las excepciones heredan de `INEError`, así que basta un
`except INEError` para capturar cualquier fallo de la librería.

| Excepción              | Cuándo                                                                 |
| ---------------------- | ---------------------------------------------------------------------- |
| `INEError`             | Raíz de la jerarquía. Base para cualquier fallo.                       |
| `INEConnectionError`   | Red / timeout / DNS / reset de conexión.                               |
| `INEHTTPError`         | Respuesta HTTP 4xx/5xx. Expone `.status`, `.url` y `.body`.            |
| `INENotFoundError`     | Recurso no encontrado (HTTP 404). Subclase de `INEHTTPError`.          |
| `INELogicalError`      | El INE respondió `200` con un mensaje de error lógico (rareza nº 1).   |
| `INEVolumeError`       | Subclase de `INELogicalError`: la tabla es demasiado grande ("restricciones de volumen"). Usa `download_table`. |
| `INEParseError`        | La respuesta no es JSON o no tiene la forma esperada.                  |

```python
from ine import Client
from ine.errors import INEConnectionError, INENotFoundError, INEError

with Client() as client:
    try:
        datos = client.datos.serie("0")  # id inválido
    except INENotFoundError:
        print("La serie no existe.")
    except INEConnectionError:
        print("No se pudo contactar con el INE (red).")
    except INEError as err:
        print(f"Otro fallo: {err}")
```

Importa las excepciones desde `ine.errors`:

```python
from ine.errors import (
    INEError,
    INEConnectionError,
    INEHTTPError,
    INENotFoundError,
    INELogicalError,
    INEParseError,
)
```

---

## Parámetros del INE

Varios métodos aceptan estos parámetros de *query* del INE (todos opcionales):

| Parámetro | Valores válidos                           | Significado                                                |
| --------- | ----------------------------------------- | ---------------------------------------------------------- |
| `det`     | `"0"` / `"1"` / `"2"`                     | Nivel de detalle (básico / detallado / muy detallado).    |
| `tip`     | `"A"` / `"M"` / `"AM"`                    | Tipo de respuesta: amigable / metadatos / ambos.          |
| `nult`    | `int`                                     | Devuelve los `nult` últimos datos o periodos.             |
| `p`       | `"1"` / `"3"` / `"6"` / `"12"`            | Periodicidad: mensual / trimestral / bianual / anual.     |
| `date`    | `["aaaammdd:aaaammdd"]`                   | Rango de fechas (el final es opcional: `aaaammdd:`).       |
| `tv`      | `["id_variable:id_valor", ...]`           | Filtros variable:valor (repetibles).                       |
| `filtros` | `list[(var, [valores])]` → param `g`      | Grupos OR (mismo grupo) / AND (grupos distintos).          |
| `page`    | `int`                                     | Página de un listado paginado (hasta 500 elem./página).    |
| `raw`     | `bool`                                    | Si es `True`, devuelve el `dict` crudo del INE (sin modelo). |

**Filtros `g`** (parámetro `filtros`): una lista de grupos `(variable, valores)`.

- Varios valores en un **mismo** grupo → **OR** (`g1=["115:29","115:30"]`).
- Varios **grupos** → **AND** (`g1=...` + `g2="3:84"`).
- `valores=None` → todos los valores de esa variable (`g3="762:"`).

```python
client.datos.metadata_operacion(
    "IPC", p="1", nult=12,
    filtros=[("115", ["29", "30"]), ("3", ["84"])],
)
```

---

## Cobertura de endpoints

### Soportados (26)

| Dominio       | Método (namespace)              | Recurso                          |
| ------------- | ------------------------------- | -------------------------------- |
| **OPERACIONES** | `client.operaciones.list()`   | `OPERACIONES_DISPONIBLES`        |
|               | `client.operaciones.get(id)`    | `OPERACION/{id}`                 |
| **SERIES**    | `client.series.get(id)`         | `SERIE/{id}`                     |
|               | `client.series.by_operacion(op)`| `SERIES_OPERACION/{op}`          |
|               | `client.series.by_tabla(id)`    | `SERIES_TABLA/{id}`              |
|               | `client.series.valores(id)`     | `VALORES_SERIE/{id}`             |
|               | `client.series.metadata_operacion(op, filtros=...)` | `SERIE_METADATAOPERACION/{op}` |
| **DATOS**     | `client.datos.tabla(id)`        | `DATOS_TABLA/{id}`               |
|               | `client.datos.serie(id, ...)`   | `DATOS_SERIE/{id}`               |
|               | `client.datos.metadata_operacion(op, filtros=...)`  | `DATOS_METADATAOPERACION/{op}` |
| **MAESTROS**  | `client.maestros.escalas()`     | `ESCALAS`                        |
|               | `client.maestros.escala(id)`    | `ESCALA/{id}`                    |
|               | `client.maestros.unidades()`    | `UNIDADES`                       |
|               | `client.maestros.unidad(id)`    | `UNIDAD/{id}`                    |
|               | `client.maestros.unidades_operacion(op)` | `UNIDADES_OPERACION/{op}` |
|               | `client.maestros.periodo(id)`   | `PERIODO/{id}`                   |
|               | `client.maestros.periodicidades()` | `PERIODICIDADES`              |
|               | `client.maestros.periodicidad(id)` | `PERIODICIDAD/{id}`           |
|               | `client.maestros.clasificaciones()` | `CLASIFICACIONES`            |
|               | `client.maestros.clasificaciones_operacion(op)` | `CLASIFICACIONES_OPERACION/{op}` |
| **PUBLICACIONES** | `client.publicaciones.publicaciones()` | `PUBLICACIONES`            |
|               | `client.publicaciones.publicaciones_operacion(op)` | `PUBLICACIONES_OPERACION/{op}` |
|               | `client.publicaciones.publicacion_fecha(id)` | `PUBLICACIONFECHA_PUBLICACION/{id}` |
| **VARIABLES** | `client.variables.variables()`  | `VARIABLES`                     |
|               | `client.variables.variables_operacion(op)` | `VARIABLES_OPERACION/{op}` |
|               | `client.variables.variable(id)` | `VARIABLE/{id}` (no documentado) |

`client.tablas.by_operacion(operacion)` también está disponible, pero devuelve `list[dict]`
crudo (el INE no documenta un esquema estable para `TABLAS_OPERACION`).

> `client.maestros` incluye **7 endpoints no documentados** en el OpenAPI oficial
> (escalas, unidades, periodos y periodicidad individuales), descubiertos empíricamente.

### Pendientes (aún no cubiertos)

`TABLAS` (resto: grupos/valores de tabla + modelo `Tabla`) y `VALORES`.

> **Honesto:** este cliente aún no cubre toda la API Tempus. Los dominios
> pendientes se irán añadiendo en próximas versiones.

---

## Configuración

Todos los parámetros del constructor son *keyword-only* (la firma es estable
entre versiones):

```python
from ine import Cache, Client, Lang

client = Client(
    lang=Lang.ES,                  # idioma de los textos de la respuesta
    base_url="https://servicios.ine.es",  # host del servicio Tempus
    timeout=10.0,                  # timeout por petición, en segundos
    retries=3,                     # reintentos sobre GET idempotente (red + 429 + 5xx)
    headers={"X-Custom": "..."},   # cabeceras extra
    cache=Cache(ttl=300),          # cache en memoria opt-in (None = sin cache, por defecto)
    httpx_client=None,             # cliente httpx inyectado (DI para tests/config avanzada)
)
```

- **`lang`** — `Lang.ES|EN|CA|GL|EU`. Determina el segmento `/js/{lang}/` de las
  URLs y el idioma de los textos.
- **`retries`** — reintentos automáticos sobre GET idempotente ante errores de
  red y `429`/`5xx`, con *backoff* y respeto a `Retry-After`. `0` los desactiva.
  Solo aplica cuando el cliente construye su propio `httpx.Client`.
- **`httpx_client`** — inyección de dependencias: si pasas tu propio
  `httpx.Client`, se respeta tal cual (sin reintentos ni cabeceras propias).
  Útil para tests (con `respx`) o para configuración avanzada del transporte.

El **gestor de contexto** cierra la conexión HTTP al salir:

```python
with Client() as client:   # abre
    ...
# cierra automáticamente
```

---

## Cache (opt-in)

Para no repetir peticiones idénticas al INE dentro de un mismo proceso (menos
latencia y carga), activa un **cache en memoria con TTL** pasando un objeto
`Cache`. Por defecto **está desactivado** (`cache=None`) — nunca te servirá
datos *stale* sin que tú lo pidas:

```python
from ine import Cache, Client

with Client(cache=Cache(ttl=300)) as client:   # cachea 5 min
    a = client.series.by_operacion("IPC")     # → petición HTTP
    b = client.series.by_operacion("IPC")     # → cache (0 peticiones)
```

- **`Cache(*, ttl=300, maxsize=None)`** — `ttl` en segundos; `maxsize` opcional
  (evicción FIFO cuando se alcanza).
- Solo se cachean **las respuestas válidas**; los errores (`INEError`) se
  relanzan siempre (nunca se cachean).
- Es **memoria por proceso** (se pierde al cerrar). La misma instancia `Cache`
  puede compartirirse entre varios `Client` (sync y async).
- El modelado pydantic se re-ejecuta sobre el dato cacheado (barato); si
  necesitas el JSON crudo sin re-validar, usa `raw=True`.

---

## Descarga de ficheros (CSV / PC-Axis / XLSX)

Para tablas **muy grandes** que la API JSON rechaza ("restricciones de volumen",
p. ej. el Padrón, id `68535`) o cuando necesitas el formato oficial, descarga el
fichero directamente. Es un **servicio distinto** (`ine.es/jaxiT3/files`, no la
API Tempus JSON) y la descarga es por **streaming**:

```python
from ine import Client, Format

with Client() as client:
    # Streama por chunks a fichero (seguro para decenas de MB) → devuelve Path
    path = client.download_table("68535", fmt=Format.CSV_BDSC, path="padron.csv")

    # O a bytes en memoria (cuidado con tablas muy grandes)
    data = client.download_table("68535", fmt=Format.PX)   # → bytes
```

- **`Format`**: `CSV_BDSC` (CSV con cabecera, separador `;`), `CSV_BD`, `PX`
  (PC-Axis), `XLSX`.
- `path` dado → streama al fichero y devuelve `pathlib.Path`; `path=None` →
  `bytes` (se carga entero en memoria).
- `lang` por defecto es el del cliente; los bytes son crudos (el charset del INE
  es inconsistente: declara ISO-8859-15 pero lleva BOM UTF-8).
- Errores: `INENotFoundError` (404), `INEHTTPError`, `INEConnectionError`.
- **Cuándo usar esto vs `client.datos.tabla`**: para tablas normales, `datos.tabla`
  es mejor (filtrable con `nult`/`date`/`tv`, tipado). `download_table` es la salida
  para tablas bloqueadas por volumen o cuando quieres el fichero oficial.

---

## Licencia

- El **código** de este cliente está bajo la licencia **MIT** (ver
  [`LICENSE`](LICENSE)).
- Los **datos** del INE distribuidos a través de su API están bajo la licencia
  **Creative Commons Attribution 4.0 (CC BY 4.0)**. Al usarlos debes
  **atribuirlos al INE** (Instituto Nacional de Estadística). Consulta los
  [términos de reutilización del INE](https://www.ine.es/dyngs/AYU/index.htm?cid=125).

> Esta librería no está afiliada al INE. Es un cliente de la comunidad.

---

## Contribuir

Las contribuciones son bienvenidas. Configuración del entorno:

```bash
uv sync
```

Los *gates* de CI que debe pasar cualquier cambio son:

```bash
uv run ruff check . && uv run mypy ine && uv run pytest
```
