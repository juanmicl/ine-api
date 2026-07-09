# ine-api: Cliente Python para la API Tempus del INE — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir el actual `ine/main.py` (20 líneas, 3 endpoints, sin robustez) en un cliente Python idiomático, tipado, robusto y con cobertura completa de la API Tempus del INE (24 endpoints del spec oficial + 9 endpoints no documentados descubiertos empíricamente = 33).

**Architecture:** Un par `Client` (sync) / `AsyncClient` (async) que delegan en un único `Backend` (la costura I/O), con funciones puras compartidas para URLs/params/parsing. Modelos **pydantic v2** con `alias_generator=to_snake` y `extra="ignore"` para domesticar el esquema irregular del INE (PascalCase, `FK_`/`T3_`, `Fecha` epoch, campos opcionales). Servicios por dominio (operaciones, series, datos, tablas, variables, valores, maestros, publicaciones).

**Tech Stack:** Python ≥3.12 · `httpx` (HTTP) · `httpx-retries` (backoff) · `pydantic` v2 (modelos) · `respx` (tests) · `ruff` + `mypy` + `pytest` (tooling) · `uv` (gestión de deps).

## Global Constraints

- **Python ≥3.12** (floor actual de `pyproject.toml`). Sin compatibilidad con versiones anteriores.
- **Gestión de dependencias con `uv`** (`uv add`, `uv add --dev`, `uv run pytest`). El repo ya usa `uv.lock`.
- **Idiomas válidos del INE:** `ES`, `EN`, `CA`, `GL`, `EU`. Exponer como `enum` (`Lang`), nunca string suelto.
- **Base URL por defecto:** `https://servicios.ine.es`. Debe ser configurable (tests, futuro cambio de host).
- **`follow_redirects=True` por defecto** (la API hace 301 al resolver códigos alfanuméricos → id numérico; ver hallazgo H2).
- **La API devuelve HTTP 200 incluso en errores lógicos** (body = string JSON `"La operación indicada no existe (X)"`). `raise_for_status()` **no basta**: el `Backend` debe validar la forma de la respuesta (ver H1).
- **404 devuelve HTML, no JSON.** `raise_for_status()` sí atrapa estos (status 404); traducir a `INEHTTPError`/`INENotFoundError`.
- **Paginación:** 4 listados usan `page` (500 elem/página). **No hay campo `total`**: el paginador para al recibir una página con `<500` elementos.
- **Licencia de los datos:** CC BY 4.0 (atribución INE). La librería es código propio del usuario.
- **`extra="ignore"` obligatorio** en todos los modelos pydantic: el INE añade campos sin avisar y el spec tiene bugs (`additionalProperties` nunca es `false`).
- **No exponer `httpx` en la API pública:** ni tipos en firmas, ni excepciones. El usuario solo importa de `ine`.
- **Namespaces (`client.series`, `client.datos`, ...) se introducen en la Fase 6**, cuando se superen ~10 métodos. Hasta entonces, métodos planos sobre `Client`.

## Hallazgos empíricos de la API (condicionan el diseño)

- **H1 — 200-on-error:** `GET /wstempus/js/ES/GRUPOS` → HTTP 200, body `"La operación indicada no existe (GRUPOS)"`. Discriminador: si `response.json()` es `str` → error lógico; si es `list` → dato.
- **H2 — Redirects:** `SERIES_OPERACION/IPC` → 301 → 200 (con `follow_redirects`). Sin ello, falla.
- **H3 — HTML 404:** `DATOS_SERIE/<id-invalido>` → 404 con `<!DOCTYPE html>`. `raise_for_status()` lo atrapa; no llamar `.json()` antes.
- **H4 — Sin total en paginación:** los listados paginados no indican cuántas páginas hay.
- **H5 — Bugs del spec OpenAPI:** `NotasJSON.required` cita `Codigo` inexistente; `T3_PubFechaAct` es `integer` (debería ser `string`); `TablasJSON.Codigo` es a la vez `nullable` y `required`; `Anyo_Periodo_ini` es `string` (los demás `Anyo*` son `integer`); ningún schema fija `additionalProperties`. → Consecuencia: `extra="ignore"`, no confiar en `required`, y ofrecer `raw=True`.
- **H6 — `Codigo` no es único:** `TMOV` aparece 3 veces en `OPERACIONES_DISPONIBLES`. La clave real es `Id`. Documentar; nunca indexar por `Codigo`.

## Estructura objetivo del paquete

```
ine/
  __init__.py          # exports públicos: Client, AsyncClient, Lang, errors, models.*
  errors.py            # jerarquía INEError
  _config.py           # Lang enum, Config dataclass
  _backend.py          # Backend (sync) + AsyncBackend (async): la única costura I/O
  _urls.py             # builders de path y params (PUROS, compartidos sync/async)
  _paginator.py        # iterador perezoso para listados paginados (<500 stop)
  _filters.py          # FiltroGrupo: builder tipado del param `g`
  client.py            # Client (sync) — wire-up config+backend+services
  async_client.py      # AsyncClient (async) — espejo
  services/
    __init__.py
    _base.py           # BaseService(backend, config)
    operaciones.py     # OPERACIONES (2 spec)
    series.py          # SERIES (5 spec)
    datos.py           # DATOS DE SERIES (3 spec)
    tablas.py          # TABLAS (3 spec)
    variables.py       # VARIABLES (2 spec + 1 simple no doc)
    valores.py         # VALORES (3 spec)
    maestros.py        # ESCALAS/UNIDADES/PERIODOS/PERIODICIDADES (no doc: list+simple) + CLASIFICACIONES/PERIODICIDADES spec
    publicaciones.py   # PUBLICACIONES (3 spec)
  models/
    __init__.py
    _base.py           # _BaseModel: alias_generator=to_snake, extra="ignore", populate_by_name
    operaciones.py  series.py  datos.py  tablas.py
    variables.py    valores.py  maestros.py  publicaciones.py
tests/
  conftest.py          # fixtures respx + respuestas capturadas
  test_config.py test_errors.py test_backend.py
  test_client_sync.py test_client_async.py
  test_models.py test_paginator.py test_filters.py
```

**Notación de prefijos:** `_` = interno (no exportar). `client.py`/`async_client.py`/`errors.py`/`models/` = API pública.

**Staging:** La Fase 1 mantiene `ine/main.py` reexportando `Client` por compatibilidad con `hello.py`; se elimina en la Fase 6 al final.

---

# FASE 1 — Fundamentos y robustez (sin models, sigue devolviendo `dict`/`list`)

> Objetivo: cerrar bugs latentes (fuga de recursos, sin timeout) e implantar el manejo de errores que la API requiere (H1/H2/H3). El `Client` sigue devolviendo JSON nativo, pero ya robusto.

### Task 1.1: Tooling del proyecto

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/__init__.py` (vacío)

**Interfaces:** N/A (config).

- [ ] **Step 1: Añadir dependencias de runtime y dev con `uv`**

```bash
uv add pydantic httpx-retries
uv add --dev ruff pytest mypy respx
```

- [ ] **Step 2: Añadir configuración de tooling al final de `pyproject.toml`**

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true
```

- [ ] **Step 3: Corregir el `description` placeholder de `pyproject.toml`**

Cambiar `description = "Add your description here"` por:
```toml
description = "Cliente Python para la API Tempus del INE (Instituto Nacional de Estadística de España)"
```

- [ ] **Step 4: Verificar que las herramientas corren**

```bash
uv run ruff check .
uv run pytest --co
uv run mypy ine
```
Expected: ruff sin errores (o solo warnings menores de `hello.py`); pytest lista 0 tests; mypy puede reportar `ine/main.py` sin tipos (aceptable por ahora).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: añade tooling (ruff/pytest/mypy) y deps (pydantic, httpx-retries, respx)"
```

---

### Task 1.2: Enum `Lang` y dataclass `Config`

**Files:**
- Create: `ine/_config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `ine._config.Lang` (enum `ES|EN|CA|GL|EU`), `ine._config.Config` (dataclass con `lang: Lang`, `base_url: str`, `timeout: float`, `follow_redirects: bool`, `user_agent: str`, `headers: Mapping[str,str]`).

- [ ] **Step 1: Escribir el test que falla**

```python
# tests/test_config.py
from ine._config import Config, Lang


def test_lang_values():
    assert Lang.ES.value == "ES"
    assert Lang.EN.value == "EN"
    assert {m.value for m in Lang} == {"ES", "EN", "CA", "GL", "EU"}


def test_config_defaults():
    c = Config()
    assert c.lang is Lang.ES
    assert c.base_url == "https://servicios.ine.es"
    assert c.timeout == 10.0
    assert c.follow_redirects is True
    assert "ine-api" in c.user_agent


def test_config_custom():
    c = Config(lang=Lang.EN, base_url="https://example.test", timeout=5.0)
    assert c.lang is Lang.EN
    assert c.base_url == "https://example.test"
```

- [ ] **Step 2: Verificar que falla**

```bash
uv run pytest tests/test_config.py -v
```
Expected: FAIL (`ModuleNotFoundError: No module named 'ine._config'`).

- [ ] **Step 3: Implementar `_config.py`**

```python
# ine/_config.py
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class Lang(str, Enum):
    ES = "ES"
    EN = "EN"
    CA = "CA"
    GL = "GL"
    EU = "EU"


_USER_AGENT = "ine-api/0.1.0"


@dataclass(frozen=True)
class Config:
    lang: Lang = Lang.ES
    base_url: str = "https://servicios.ine.es"
    timeout: float = 10.0
    follow_redirects: bool = True
    user_agent: str = _USER_AGENT
    headers: Mapping[str, str] = field(default_factory=dict)
```

- [ ] **Step 4: Verificar que pasa**

```bash
uv run pytest tests/test_config.py -v
```
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add ine/_config.py tests/test_config.py
git commit -m "feat(config): añade enum Lang y dataclass Config"
```

---

### Task 1.3: Jerarquía de errores `INEError`

**Files:**
- Create: `ine/errors.py`
- Test: `tests/test_errors.py`

**Interfaces:**
- Produces: `INEError` (raíz), `INEConnectionError`, `INEHTTPError` (con `status`, `url`, `body`), `INENotFoundError(INEHTTPError)`, `INEParseError`, `INELogicalError` (para los 200-on-error de H1).

- [ ] **Step 1: Escribir el test que falla**

```python
# tests/test_errors.py
import pytest

from ine.errors import (
    INEConnectionError,
    INEError,
    INEHTTPError,
    INELogicalError,
    INENotFoundError,
    INEParseError,
)


def test_hierarchy_root():
    assert issubclass(INEConnectionError, INEError)
    assert issubclass(INEHTTPError, INEError)
    assert issubclass(INEParseError, INEError)
    assert issubclass(INELogicalError, INEError)


def test_not_found_is_http_error():
    assert issubclass(INENotFoundError, INEHTTPError)


def test_http_error_carries_context():
    err = INEHTTPError(status=500, url="https://x", body="boom")
    assert err.status == 500
    assert err.url == "https://x"
    assert err.body == "boom"
    assert "500" in str(err)


def test_logical_error_message():
    err = INELogicalError("La operación indicada no existe (GRUPOS)")
    assert "GRUPOS" in str(err)


def test_errors_raisable():
    with pytest.raises(INENotFoundError):
        raise INENotFoundError(status=404, url="u", body="b")
```

- [ ] **Step 2: Verificar que falla**

```bash
uv run pytest tests/test_errors.py -v
```
Expected: FAIL (`ModuleNotFoundError: ine.errors`).

- [ ] **Step 3: Implementar `errors.py`**

```python
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
```

- [ ] **Step 4: Verificar que pasa**

```bash
uv run pytest tests/test_errors.py -v
```
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add ine/errors.py tests/test_errors.py
git commit -m "feat(errors): añade jerarquía INEError"
```

---

### Task 1.4: `Backend` (la costura I/O, con H1/H2/H3)

**Files:**
- Create: `ine/_backend.py`
- Test: `tests/test_backend.py`

**Interfaces:**
- Consumes: `ine._config.Config`, `ine.errors.*`.
- Produces: `ine._backend.Backend` con `__init__(self, config, httpx_client=None)`, `get(self, path, params=None) -> list | dict` (datos válidos; traduce todo error a `INEError`), y `close()`.

**Comportamiento crítico:**
1. `follow_redirects=True` desde `config`.
2. `raise_for_status()` primero → traduce `httpx.HTTPStatusError` (status 404→`INENotFoundError`, otro→`INEHTTPError`).
3. Content-type guard: si no es `application/json` → `INEParseError` (defensa ante HTML inesperado).
4. `data = response.json()`; si `isinstance(data, str)` → `INELogicalError(data)` (H1).
5. Errores de red → `INEConnectionError`.

- [ ] **Step 1: Escribir el test que falla**

```python
# tests/test_backend.py
import httpx
import pytest
import respx

from ine._backend import Backend
from ine._config import Config
from ine.errors import INEConnectionError, INEHTTPError, INELogicalError, INENotFoundError


def make_backend():
    return Backend(Config())


@respx.mock
def test_get_returns_list():
    respx.get("https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=[{"Id": 4, "Nombre": "Op"}])
    )
    data = make_backend().get("/wstempus/js/ES/OPERACIONES_DISPONIBLES")
    assert data == [{"Id": 4, "Nombre": "Op"}]


@respx.mock
def test_get_translates_404():
    respx.get("https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/0").mock(
        return_value=httpx.Response(404, text="<html>404</html>")
    )
    with pytest.raises(INENotFoundError):
        make_backend().get("/wstempus/js/ES/DATOS_SERIE/0")


@respx.mock
def test_get_translates_500():
    respx.get("https://servicios.ine.es/wstempus/js/ES/X").mock(
        return_value=httpx.Response(500, text="err")
    )
    with pytest.raises(INEHTTPError) as exc:
        make_backend().get("/wstempus/js/ES/X")
    assert not isinstance(exc.value, INENotFoundError)


@respx.mock
def test_get_raises_logical_error_on_200_string_body():
    respx.get("https://servicios.ine.es/wstempus/js/ES/GRUPOS").mock(
        return_value=httpx.Response(200, json="La operación indicada no existe (GRUPOS)")
    )
    with pytest.raises(INELogicalError):
        make_backend().get("/wstempus/js/ES/GRUPOS")


@respx.mock
def test_get_raises_parse_error_on_html_200():
    respx.get("https://servicios.ine.es/wstempus/js/ES/X").mock(
        return_value=httpx.Response(200, text="<html>oops</html>",
                                    headers={"content-type": "text/html"})
    )
    with pytest.raises(INEParseError):
        make_backend().get("/wstempus/js/ES/X")


@respx.mock
def test_get_translates_connection_error():
    respx.get("https://servicios.ine.es/wstempus/js/ES/X").mock(
        side_effect=httpx.ConnectError("boom")
    )
    with pytest.raises(INEConnectionError):
        make_backend().get("/wstempus/js/ES/X")


@respx.mock
def test_get_sends_params():
    route = respx.get("https://servicios.ine.es/wstempus/js/ES/X").mock(
        return_value=httpx.Response(200, json=[])
    )
    make_backend().get("/wstempus/js/ES/X", params={"det": "1", "page": 2})
    assert route.calls.last.request.url.params["det"] == "1"
    assert route.calls.last.request.url.params["page"] == "2"


def test_backend_follows_redirects_from_config(monkeypatch):
    seen = {}
    real_init = httpx.Client.__init__

    def spy(self, *a, **kw):
        seen["follow_redirects"] = kw.get("follow_redirects")
        return real_init(self, *a, **kw)

    monkeypatch.setattr(httpx.Client, "__init__", spy)
    Backend(Config(follow_redirects=True))
    assert seen["follow_redirects"] is True
```

- [ ] **Step 2: Verificar que falla**

```bash
uv run pytest tests/test_backend.py -v
```
Expected: FAIL (`ModuleNotFoundError: ine._backend`).

- [ ] **Step 3: Implementar `_backend.py`**

```python
# ine/_backend.py
from __future__ import annotations

from typing import Any, Mapping

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

    def get(self, path: str, params: Mapping[str, Any] | None = None) -> list | dict:
        try:
            response = self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            raise INEConnectionError(str(exc)) from exc
        self._raise_for_status(response)
        self._guard_json(response)
        data = response.json()
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
```

- [ ] **Step 4: Verificar que pasa**

```bash
uv run pytest tests/test_backend.py -v
```
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add ine/_backend.py tests/test_backend.py
git commit -m "feat(backend): añade Backend con manejo de errores H1/H2/H3"
```

---

### Task 1.5: Refactor de `Client` sobre `Config` + `Backend` (context manager, DI)

**Files:**
- Modify: `ine/main.py` (reexport temporal para `hello.py`)
- Create: `ine/client.py`
- Test: `tests/test_client_sync.py`

**Interfaces:**
- Produces: `ine.client.Client(*, lang=Lang.ES, base_url=..., timeout=10.0, follow_redirects=True, headers=None, httpx_client=None)`; context manager; `.get_operaciones()`, `.get_tablas(operacion)`, `.get_datos_tabla(tabla_id)` siguen devolviendo `list` (compatibilidad), pero ahora robustos.

- [ ] **Step 1: Escribir el test que falla**

```python
# tests/test_client_sync.py
import httpx
import pytest
import respx

from ine._config import Lang
from ine.client import Client
from ine.errors import INELogicalError


def make_client():
    return Client(lang=Lang.ES)


@respx.mock
def test_get_operaciones():
    respx.get("https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=[{"Id": 4}])
    )
    assert make_client().get_operaciones() == [{"Id": 4}]


@respx.mock
def test_get_tablas_passes_operacion_in_path():
    route = respx.get("https://servicios.ine.es/wstempus/js/ES/TABLAS_OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[{"Id": 1}])
    )
    Client().get_tablas("IPC")
    assert route.called


@respx.mock
def test_get_datos_tabla_passes_params():
    # compat: firma actual sin params extra, pero el path debe contener el id
    route = respx.get("https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/24077").mock(
        return_value=httpx.Response(200, json=[{"Data": []}])
    )
    Client().get_datos_tabla("24077")
    assert route.called


def test_client_is_context_manager():
    with Client() as c:
        assert isinstance(c, Client)
    # debe poder cerrarse sin error


def test_client_uses_injected_httpx_client():
    injected = httpx.Client(base_url="https://servicios.ine.es")
    c = Client(httpx_client=injected)
    assert c._backend._client is injected  # no creó uno nuevo


@respx.mock
def test_client_lang_en_in_path():
    route = respx.get("https://servicios.ine.es/wstempus/js/EN/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=[])
    )
    Client(lang=Lang.EN).get_operaciones()
    assert route.called


@respx.mock
def test_client_propagates_logical_error():
    respx.get("https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json="La operación indicada no existe (X)")
    )
    with pytest.raises(INELogicalError):
        Client().get_operaciones()
```

- [ ] **Step 2: Verificar que falla**

```bash
uv run pytest tests/test_client_sync.py -v
```
Expected: FAIL (`ModuleNotFoundError: ine.client`).

- [ ] **Step 3: Implementar `client.py`**

```python
# ine/client.py
from __future__ import annotations

from typing import Any, Mapping

import httpx

from ine._backend import Backend
from ine._config import Config, Lang


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
    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._backend.close()

    # --- endpoints (compatibles con la API actual; aún devuelven list) ---
    def get_operaciones(self) -> list[dict[str, Any]]:
        return self._backend.get(f"/wstempus/js/{self._config.lang.value}/OPERACIONES_DISPONIBLES")

    def get_tablas(self, operacion: str) -> list[dict[str, Any]]:
        return self._backend.get(f"/wstempus/js/{self._config.lang.value}/TABLAS_OPERACION/{operacion}")

    def get_datos_tabla(self, tabla_id: str) -> list[dict[str, Any]]:
        return self._backend.get(f"/wstempus/js/{self._config.lang.value}/DATOS_TABLA/{tabla_id}")
```

- [ ] **Step 4: Hacer que `ine/main.py` reexporte `Client` (compat con `hello.py`)**

Reemplazar TODO el contenido de `ine/main.py` por:

```python
# ine/main.py
from ine.client import Client, Lang  # noqa: F401  (compatibilidad hacia atrás)
```

- [ ] **Step 5: Verificar que pasa y que `hello.py` sigue importando**

```bash
uv run pytest tests/test_client_sync.py tests/test_backend.py tests/test_config.py tests/test_errors.py -v
uv run python -c "from ine.main import Client; print('ok')"
```
Expected: todos PASS; el `-c` imprime `ok`.

- [ ] **Step 6: Commit**

```bash
git add ine/client.py ine/main.py tests/test_client_sync.py
git commit -m "feat(client): refactor Client sobre Config+Backend con context manager y DI"
```

---

# FASE 2 — Tests de contrato de los 3 endpoints existentes

### Task 2.1: Fixtures y tests de contrato

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_contract.py`

**Interfaces:** Consumes `Client`.

**Objetivo:** Fijar el contrato real de los 3 endpoints (formas de respuesta capturadas del INE) para detectar regresiones al introducir modelos en la Fase 3.

- [ ] **Step 1: Crear `conftest.py` con un helper de mock**

```python
# tests/conftest.py
import httpx
import pytest
import respx


@pytest.fixture
def mock_ine():
    """Fixture que mockingea https://servicios.ine.es para un test."""
    with respx.mock:
        yield respx
```

- [ ] **Step 2: Escribir tests de contrato con respuestas capturadas (formas reales)**

```python
# tests/test_contract.py
import httpx

from ine.client import Client

BASE = "https://servicios.ine.es/wstempus/js/ES"


def test_contract_operaciones(mock_ine):
    mock_ine.get(f"{BASE}/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=[{
            "Id": 4, "Cod_IOE": "30147",
            "Nombre": "Estadística de Efectos de Comercio Impagados",
            "Codigo": "ECE", "Url": "https://...",
        }])
    )
    ops = Client().get_operaciones()
    assert ops[0]["Id"] == 4
    assert ops[0]["Codigo"] == "ECE"


def test_contract_tablas(mock_ine):
    mock_ine.get(f"{BASE}/TABLAS_OPERACION/IPC").mock(
        return_value=httpx.Response(200, json=[{
            "Id": 24077, "Nombre": "Índice general nacional",
            "Codigo": "NAC", "FK_Periodicidad": 1,
        }])
    )
    tablas = Client().get_tablas("IPC")
    assert tablas[0]["Id"] == 24077


def test_contract_datos_tabla(mock_ine):
    mock_ine.get(f"{BASE}/DATOS_TABLA/24077").mock(
        return_value=httpx.Response(200, json=[{
            "COD": "IPC53262", "Nombre": "Serie",
            "Data": [{"Fecha": 1293840000000, "Valor": 0.5, "Anyo": 2011, "FK_Periodo": 1}],
        }])
    )
    datos = Client().get_datos_tabla("24077")
    assert datos[0]["COD"] == "IPC53262"
    assert datos[0]["Data"][0]["Anyo"] == 2011
```

- [ ] **Step 3: Verificar que pasan**

```bash
uv run pytest tests/test_contract.py -v
```
Expected: PASS (3 tests).

- [ ] **Step 4: Commit**

```bash
git add tests/conftest.py tests/test_contract.py
git commit -m "test: tests de contrato para los 3 endpoints existentes"
```

---

# FASE 3 — Modelos pydantic v2 + `raw=True`

> Objetivo: tipar las respuestas con modelos Pythonicos. Campos en `snake_case`; las claves PascalCase irregulares del INE (`FK_Periodicidad`, `Cod_IOE`, `FK_PubFechaAct`, `Anyo_Periodo_ini`...) se normalizan a snake vía un `model_validator(mode="before")` que aplica `to_snake` a las **claves de entrada** (PascalCase→snake es determinista; el reverso no lo es, por lo que `alias_generator` no sirve aquí). `extra="ignore"`, `Fecha`→`datetime`. Mantener `raw=True` como válvula (H5).

### Task 3.1: `_BaseModel` y conversión `Fecha` epoch→`datetime`

**Files:**
- Create: `ine/models/__init__.py`
- Create: `ine/models/_base.py`
- Test: `tests/test_models_base.py`

**Interfaces:**
- Produces: `ine.models._base._BaseModel` (pydantic BaseModel que normaliza claves de entrada a snake_case vía `model_validator(before)` + `extra="ignore"` + `populate_by_name=True`) y `ine.models._base.ConFecha` (mixin que convierte epoch-ms → `datetime` para el campo `fecha`).

> **Nota de diseño (verificada empíricamente):** `alias_generator=to_snake` NO funciona para el INE: `alias_generator` mapea *nombre de campo → alias*, y `to_snake("fk_periodicidad") == "fk_periodicidad"`, así que el alias jamás coincide con la clave real `FK_Periodicidad` (la validación falla con "Field required"). La forma correcta y sin pérdidas es **normalizar las claves de entrada** con `to_snake` (PascalCase→snake SÍ es recuperable; `FK_PubFechaAct → fk_pub_fecha_act`, `Cod_IOE → cod_ioe`, `Anyo_Periodo_ini → anyo_periodo_ini`). NUNCA uses `alias_generator` aquí, y NUNCA inventes una función inversa (snake→Pascal) — es con pérdidas para acrónimos/multipalabras.

- [ ] **Step 1: Escribir el test que falla**

```python
# tests/test_models_base.py
from datetime import datetime, timezone

from ine.models._base import _BaseModel


def test_alias_to_snake_and_populate_by_name():
    class M(_BaseModel):
        fk_periodicidad: int
        t3_operacion: str

    m = M.model_validate({"FK_Periodicidad": 1, "T3_Operacion": "IPC"})
    assert m.fk_periodicidad == 1
    assert m.t3_operacion == "IPC"
    # también acepta el nombre pythonic
    m2 = M(fk_periodicidad=2, t3_operacion="X")
    assert m2.fk_periodicidad == 2


def test_hard_ine_keys_acronyms_and_camelcase():
    # Casos que rompen un alias_generator inverso: acrónimos y CamelCase sin '_'
    class M(_BaseModel):
        cod_ioe: str | None = None
        fk_pub_fecha_act: int | None = None
        anyo_periodo_ini: str | None = None
        t3_tipo_dato: str | None = None

    m = M.model_validate({
        "Cod_IOE": "30138",
        "FK_PubFechaAct": 12597,
        "Anyo_Periodo_ini": "1961",
        "T3_TipoDato": "P",
    })
    assert m.cod_ioe == "30138"
    assert m.fk_pub_fecha_act == 12597
    assert m.anyo_periodo_ini == "1961"
    assert m.t3_tipo_dato == "P"


def test_extra_ignored():
    class M(_BaseModel):
        nombre: str

    m = M.model_validate({"Nombre": "x", "CampoRaroQueNoExiste": 123})
    assert m.nombre == "x"


def test_fecha_epoch_ms_to_datetime():
    class M(_BaseModel):
        fecha: datetime

    # 1293840000000 ms = 2011-01-01T00:00:00Z
    m = M.model_validate({"Fecha": 1293840000000})
    assert m.fecha == datetime(2011, 1, 1, tzinfo=timezone.utc)
```

- [ ] **Step 2: Verificar que falla**

```bash
uv run pytest tests/test_models_base.py -v
```
Expected: FAIL (`ModuleNotFoundError: ine.models._base`).

- [ ] **Step 3: Implementar `models/_base.py`**

Un `field_validator("*")` global **no** puede saber el tipo destino, así que el helper `Fecha` es un **mixin** `ConFecha` que los modelos con campo `fecha` heredan. La normalización de claves se hace con un `model_validator(mode="before")` (ver nota de diseño arriba):

```python
# ine/models/_base.py
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from pydantic.alias_generators import to_snake


class _BaseModel(BaseModel):
    """Base para modelos del INE.

    El INE envía claves en PascalCase irregular (``FK_Periodicidad``,
    ``Cod_IOE``, ``FK_PubFechaAct``, ``Anyo_Periodo_ini``...). Normalizamos las
    CLAVES de entrada con ``to_snake`` (PascalCase→snake es determinista), y
    declaramos los campos en snake_case. ``extra='ignore'`` descarta campos
    desconocidos (el INE añade campos sin avisar; el spec tiene bugs).
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def _normalize_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {to_snake(k): v for k, v in data.items()}
        return data


class ConFecha(_BaseModel):
    """Mixin para modelos con un campo ``fecha`` que el INE envía como epoch-ms.

    ``check_fields=False`` es necesario porque el mixin no declara ``fecha``;
    lo hacen las subclases concretas.
    """

    @field_validator("fecha", mode="before", check_fields=False)
    @classmethod
    def _epoch_ms(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return datetime.fromtimestamp(v / 1000, tz=UTC)
        return v
```

- [ ] **Step 4: Escribir el test del mixin (reemplaza el `test_fecha...` del Step 1)**

Reemplaza `test_fecha_epoch_ms_to_datetime` por:

```python
from ine.models._base import ConFecha

def test_fecha_epoch_ms_to_datetime():
    class M(ConFecha):
        fecha: datetime

    m = M.model_validate({"Fecha": 1293840000000})
    assert m.fecha == datetime(2011, 1, 1, tzinfo=timezone.utc)
```

- [ ] **Step 5: Verificar que pasa**

```bash
uv run pytest tests/test_models_base.py -v
```
Expected: PASS (3 tests).

- [ ] **Step 6: Commit**

```bash
git add ine/models/__init__.py ine/models/_base.py tests/test_models_base.py
git commit -m "feat(models): _BaseModel (alias+extra ignore) y mixin ConFecha epoch-ms"
```

---

### Task 3.2: Modelos de Operaciones y la opción `raw=True`

**Files:**
- Create: `ine/models/operaciones.py`
- Modify: `ine/client.py` (`get_operaciones` devuelve `list[Operacion]`, con `raw=False`)
- Test: `tests/test_models_operaciones.py`

**Interfaces:**
- Produces: `ine.models.operaciones.Operacion` (campos: `id:int`, `cod_ioe:str|None`, `nombre:str`, `codigo:str|None`, `url:str|None`).
- `Client.get_operaciones(*, raw: bool = False) -> list[Operacion] | list[dict]`.

- [ ] **Step 1: Escribir el test que falla**

```python
# tests/test_models_operaciones.py
import httpx

from ine.client import Client
from ine.models.operaciones import Operacion

BASE = "https://servicios.ine.es/wstempus/js/ES"


def test_operacion_model_aliases():
    op = Operacion.model_validate({
        "Id": 4, "Cod_IOE": "30147",
        "Nombre": "Efectos impagados", "Codigo": "ECE",
    })
    assert op.id == 4
    assert op.cod_ioe == "30147"
    assert op.nombre == "Efectos impagados"
    assert op.codigo == "ECE"


def test_operacion_cod_ioe_optional_empty():
    op = Operacion.model_validate({"Nombre": "X", "Codigo": "Y", "Cod_IOE": ""})
    assert op.cod_ioe == ""


def test_client_get_operaciones_returns_models(mock_ine):
    mock_ine.get(f"{BASE}/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=[{"Id": 4, "Nombre": "n", "Codigo": "c", "Cod_IOE": "i"}])
    )
    ops = Client().get_operaciones()
    assert isinstance(ops[0], Operacion)
    assert ops[0].id == 4


def test_client_get_operaciones_raw(mock_ine):
    payload = [{"Id": 4, "Nombre": "n", "Codigo": "c"}]
    mock_ine.get(f"{BASE}/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=payload)
    )
    ops = Client().get_operaciones(raw=True)
    assert ops == payload
```

- [ ] **Step 2: Verificar que falla**

```bash
uv run pytest tests/test_models_operaciones.py -v
```
Expected: FAIL (`ModuleNotFoundError: ine.models.operaciones`).

- [ ] **Step 3: Implementar el modelo**

```python
# ine/models/operaciones.py
from __future__ import annotations

from ine.models._base import _BaseModel


class Operacion(_BaseModel):
    id: int | None = None
    cod_ioe: str | None = None
    nombre: str
    codigo: str | None = None
    url: str | None = None
```

- [ ] **Step 4: Actualizar `Client.get_operaciones` con `raw`**

```python
# ine/client.py — modificar get_operaciones y el import arriba
from ine.models.operaciones import Operacion
from typing import Any, Mapping
# ...

class Client:
    # ...
    def get_operaciones(self, *, raw: bool = False):
        data = self._backend.get(
            f"/wstempus/js/{self._config.lang.value}/OPERACIONES_DISPONIBLES"
        )
        if raw:
            return data
        return [Operacion.model_validate(d) for d in data]
```

- [ ] **Step 5: Verificar que pasa**

```bash
uv run pytest tests/test_models_operaciones.py tests/test_client_sync.py -v
```
Expected: PASS. (Nota: `test_get_operaciones` en `test_client_sync.py` compara `== [{"Id":4}]`; al ahora devolver modelos, ACTUALIZA ese test en la Fase 3 — ver Step 6.)

- [ ] **Step 6: Actualizar `test_get_operaciones` en `tests/test_client_sync.py`**

```python
@respx.mock
def test_get_operaciones():
    respx.get("https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=[{"Id": 4, "Nombre": "Op"}])
    )
    from ine.models.operaciones import Operacion
    ops = make_client().get_operaciones()
    assert isinstance(ops[0], Operacion)
    assert ops[0].id == 4
```

- [ ] **Step 7: Commit**

```bash
git add ine/models/operaciones.py ine/client.py tests/test_models_operaciones.py tests/test_client_sync.py
git commit -m "feat(models): modelo Operacion + raw=True en get_operaciones"
```

---

### Task 3.3: Modelos de Datos (con `Fecha` epoch y `Data` anidado)

**Files:**
- Create: `ine/models/datos.py` (`DatosJSON`, `DatosSerieJSON`)
- Modify: `ine/client.py` (`get_datos_tabla` → `list[DatosSerie]`, con `raw`)
- Test: `tests/test_models_datos.py`

**Interfaces:**
- Produces: `DatosObservacion` (`fecha: datetime`, `valor: float`, `anyo: int`, `fk_periodo: int`, `secreto: bool=False`) y `DatosSerie` (`cod: str`, `nombre: str`, `data: list[DatosObservacion]`).
- `Client.get_datos_tabla(tabla_id, *, raw=False)`.

- [ ] **Step 1: Test que falla**

```python
# tests/test_models_datos.py
from datetime import datetime, timezone

from ine.models.datos import DatosObservacion, DatosSerie


def test_datos_observacion_fecha_epoch():
    o = DatosObservacion.model_validate({
        "Fecha": 1293840000000, "Valor": 1.5, "Anyo": 2011, "FK_Periodo": 1,
    })
    assert o.fecha == datetime(2011, 1, 1, tzinfo=timezone.utc)
    assert o.valor == 1.5
    assert o.secreto is False


def test_datos_serie_nested():
    s = DatosSerie.model_validate({
        "COD": "IPC53262", "Nombre": "n",
        "Data": [{"Fecha": 1293840000000, "Valor": 0.1, "Anyo": 2011, "FK_Periodo": 1}],
    })
    assert s.cod == "IPC53262"
    assert len(s.data) == 1
    assert isinstance(s.data[0].fecha, datetime)
```

- [ ] **Step 2: Verificar que falla** — `uv run pytest tests/test_models_datos.py -v` → FAIL.

- [ ] **Step 3: Implementar**

```python
# ine/models/datos.py
from __future__ import annotations

from datetime import datetime

from ine.models._base import ConFecha, _BaseModel


class DatosObservacion(ConFecha):
    fecha: datetime
    valor: float
    anyo: int
    fk_periodo: int
    secreto: bool = False


class DatosSerie(_BaseModel):
    cod: str
    nombre: str
    data: list[DatosObservacion] = []
```

- [ ] **Step 4: Actualizar `Client.get_datos_tabla`**

```python
# ine/client.py
from ine.models.datos import DatosSerie
# ...
    def get_datos_tabla(self, tabla_id: str, *, raw: bool = False):
        data = self._backend.get(
            f"/wstempus/js/{self._config.lang.value}/DATOS_TABLA/{tabla_id}"
        )
        if raw:
            return data
        return [DatosSerie.model_validate(d) for d in data]
```

- [ ] **Step 5: Verificar que pasa** — `uv run pytest tests/test_models_datos.py tests/test_contract.py -v` → PASS. (Actualiza `test_contract_datos_tabla` para usar `.raw=True` o ajustar aserciones a modelos.)

- [ ] **Step 6: Commit**

```bash
git add ine/models/datos.py ine/client.py tests/test_models_datos.py
git commit -m "feat(models): modelos DatosObservacion/DatosSerie con Fecha epoch"
```

---

# FASE 4 — `AsyncBackend` + `AsyncClient`

> Objetivo: ofrecer async sin duplicar lógica. Toda la lógica de URL/params/parsing ya es compartida vía `_urls.py`/`models/`.

### Task 4.1: `_urls.py` (funciones puras compartidas)

**Files:**
- Create: `ine/_urls.py`
- Test: `tests/test_urls.py`

**Interfaces:** Produce builders de path y params: `operaciones_path(lang)`, `tablas_operacion_path(lang, op)`, `datos_tabla_path(lang, id)`, `build_params(det=None, tip=None, nult=None, page=None, geo=None, det=None, ...) -> dict` (filtra `None`).

- [ ] **Step 1: Test que falla**

```python
# tests/test_urls.py
from ine._urls import (
    build_params,
    datos_tabla_path,
    operaciones_path,
    tablas_operacion_path,
)


def test_paths():
    assert operaciones_path("ES") == "/wstempus/js/ES/OPERACIONES_DISPONIBLES"
    assert tablas_operacion_path("ES", "IPC") == "/wstempus/js/ES/TABLAS_OPERACION/IPC"
    assert datos_tabla_path("EN", "24077") == "/wstempus/js/EN/DATOS_TABLA/24077"


def test_build_params_drops_none():
    assert build_params(det="1", nult=12) == {"det": "1", "nult": 12}
    assert build_params() == {}
```

- [ ] **Step 2: Verificar que falla** — `uv run pytest tests/test_urls.py -v` → FAIL.

- [ ] **Step 3: Implementar**

```python
# ine/_urls.py
from __future__ import annotations

from typing import Any


def operaciones_path(lang: str) -> str:
    return f"/wstempus/js/{lang}/OPERACIONES_DISPONIBLES"


def operacion_path(lang: str, op: str) -> str:
    return f"/wstempus/js/{lang}/OPERACION/{op}"


def tablas_operacion_path(lang: str, op: str) -> str:
    return f"/wstempus/js/{lang}/TABLAS_OPERACION/{op}"


def datos_tabla_path(lang: str, tabla_id: str) -> str:
    return f"/wstempus/js/{lang}/DATOS_TABLA/{tabla_id}"


def datos_serie_path(lang: str, serie_id: str) -> str:
    return f"/wstempus/js/{lang}/DATOS_SERIE/{serie_id}"


def series_operacion_path(lang: str, op: str) -> str:
    return f"/wstempus/js/{lang}/SERIES_OPERACION/{op}"


def build_params(**kwargs: Any) -> dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v is not None}
```

- [ ] **Step 4: Verificar que pasa** — `uv run pytest tests/test_urls.py -v` → PASS.

- [ ] **Step 5: Commit**

```bash
git add ine/_urls.py tests/test_urls.py
git commit -m "feat(urls): builders de path y params puros (compartidos sync/async)"
```

---

### Task 4.2: `AsyncBackend` y `AsyncClient`

**Files:**
- Modify: `ine/_backend.py` (añadir `AsyncBackend`)
- Create: `ine/async_client.py`
- Test: `tests/test_client_async.py`

**Interfaces:**
- Produce `ine._backend.AsyncBackend` (`async get(...)`).
- Produce `ine.async_client.AsyncClient` espejo de `Client` (`async __aenter__`/`__aexit__`).

- [ ] **Step 1: Test que falla**

```python
# tests/test_client_async.py
import httpx
import pytest
import respx

from ine.async_client import AsyncClient
from ine.models.operaciones import Operacion

BASE = "https://servicios.ine.es/wstempus/js/ES"


@respx.mock
@pytest.mark.anyio
async def test_async_get_operaciones():
    respx.get(f"{BASE}/OPERACIONES_DISPONIBLES").mock(
        return_value=httpx.Response(200, json=[{"Id": 4, "Nombre": "n", "Codigo": "c"}])
    )
    async with AsyncClient() as c:
        ops = await c.get_operaciones()
    assert isinstance(ops[0], Operacion)
    assert ops[0].id == 4
```

> Requiere `anyio` para tests async: `uv add --dev anyio`. (`anyio` ya incluye su plugin de pytest; **no** hace falta un paquete `pytest-anyio` aparte.) Añade a `pyproject.toml`:
> ```toml
> [tool.pytest.ini_options]
> anyio_backend = "asyncio"
> ```

- [ ] **Step 2: Verificar que falla** — `uv run pytest tests/test_client_async.py -v` → FAIL.

- [ ] **Step 3: Añadir `AsyncBackend` a `_backend.py`**

```python
# añadir a ine/_backend.py
class AsyncBackend:
    def __init__(self, config: Config, httpx_client: httpx.AsyncClient | None = None) -> None:
        self._config = config
        if httpx_client is None:
            httpx_client = httpx.AsyncClient(
                base_url=config.base_url,
                timeout=config.timeout,
                follow_redirects=config.follow_redirects,
                headers={"User-Agent": config.user_agent, **dict(config.headers)},
            )
        self._client = httpx_client

    async def get(self, path: str, params: Mapping[str, Any] | None = None) -> list | dict:
        try:
            response = await self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            raise INEConnectionError(str(exc)) from exc
        Backend._raise_for_status(response)
        Backend._guard_json(response)
        data = response.json()
        if isinstance(data, str):
            raise INELogicalError(data)
        return data

    async def aclose(self) -> None:
        await self._client.aclose()
```

- [ ] **Step 4: Implementar `async_client.py`**

```python
# ine/async_client.py
from __future__ import annotations

from typing import Mapping

import httpx

from ine._backend import AsyncBackend
from ine._config import Config, Lang
from ine._urls import datos_tabla_path, operaciones_path, tablas_operacion_path
from ine.models.datos import DatosSerie
from ine.models.operaciones import Operacion


class AsyncClient:
    def __init__(
        self,
        *,
        lang: Lang = Lang.ES,
        base_url: str = "https://servicios.ine.es",
        timeout: float = 10.0,
        follow_redirects: bool = True,
        headers: Mapping[str, str] | None = None,
        httpx_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._config = Config(lang=lang, base_url=base_url, timeout=timeout,
                              follow_redirects=follow_redirects, headers=headers or {})
        self._backend = AsyncBackend(self._config, httpx_client=httpx_client)

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def close(self) -> None:
        await self._backend.aclose()

    async def get_operaciones(self, *, raw: bool = False):
        data = await self._backend.get(operaciones_path(self._config.lang.value))
        return data if raw else [Operacion.model_validate(d) for d in data]

    async def get_tablas(self, operacion: str, *, raw: bool = False):
        return await self._backend.get(tablas_operacion_path(self._config.lang.value, operacion))

    async def get_datos_tabla(self, tabla_id: str, *, raw: bool = False):
        data = await self._backend.get(datos_tabla_path(self._config.lang.value, tabla_id))
        return data if raw else [DatosSerie.model_validate(d) for d in data]
```

- [ ] **Step 5: Verificar que pasa** — `uv run pytest tests/test_client_async.py -v` → PASS.

- [ ] **Step 6: Commit**

```bash
git add ine/_backend.py ine/async_client.py tests/test_client_async.py pyproject.toml uv.lock
git commit -m "feat(async): AsyncBackend + AsyncClient espejo del sync"
```

---

# FASE 5 — Resiliencia + expansión del catálogo (33 endpoints)

> Esta fase introduce patrones nuevos (reintentos, paginador, builder de filtros) y luego los servicios por dominio. Cada servicio es mecánico una vez fijado el patrón; se aportan **path + params + schema concreto** por endpoint (no "ver arriba").

### Task 5.1: Reintentos con `httpx-retries`

**Files:**
- Modify: `ine/_backend.py` (construir `transport` con reintentos)

**Criterio:** reintentar solo GET idempotente, sobre errores de red y 429/5xx, máx 3, backoff con jitter, respetar `Retry-After`.

- [ ] **Step 1: Test que falla** — mockea un `respx` route que falle 2 veces y luego 200; verifica que `Backend.get` devuelve el dato.

```python
# tests/test_retries.py
import httpx
import respx

from ine._backend import Backend
from ine._config import Config


@respx.mock
def test_retries_then_succeeds():
    route = respx.get("https://servicios.ine.es/wstempus/js/ES/X").mock(
        side_effect=[httpx.ConnectError("x"), httpx.ConnectError("y"),
                     httpx.Response(200, json=[])]
    )
    # forzamos retries=3 vía un cliente con transport propio
    data = Backend(Config()).get("/wstempus/js/ES/X")
    assert route.call_count == 3
    assert data == []
```

- [ ] **Step 2: Verificar que falla** — `uv run pytest tests/test_retries.py -v` → FAIL (no reintenta).

- [ ] **Step 3: Implementar** — usar `httpx_retries.RetryTransport` envolviendo `httpx.HTTPTransport`:

```python
# ine/_backend.py — en Backend.__init__, si no se inyecta cliente:
from httpx_retries import Retry, RetryTransport

retry = Retry(total=3, backoff_factor=0.5, respect_retry_after_header=True)
transport = RetryTransport(retry=retry, transport=httpx.HTTPTransport(retries=0))
httpx_client = httpx.Client(
    base_url=config.base_url, timeout=config.timeout,
    follow_redirects=config.follow_redirects, transport=transport,
    headers={"User-Agent": config.user_agent, **dict(config.headers)},
)
```

> **Consulta la API exacta de `httpx-retries`** con `uv run python -c "import httpx_retries; help(httpx_retries.RetryTransport)"` antes de implementar; la firma puede variar entre versiones. Ajusta el nombre del kwarg (`retry=` vs `retries=`) según corresponda.

- [ ] **Step 4: Verificar que pasa** — `uv run pytest tests/test_retries.py -v` → PASS.

- [ ] **Step 5: Commit**

```bash
git add ine/_backend.py tests/test_retries.py
git commit -m "feat(backend): reintentos con httpx-retries (red + 429/5xx)"
```

---

### Task 5.2: Paginador perezoso (stop en `<500`)

**Files:**
- Create: `ine/_paginator.py`
- Test: `tests/test_paginator.py`

**Interfaces:**
- Produce `iter_pages(fetch_page: Callable[[int], list]) -> Iterator[list]` (sinc) y `async def aiter_pages(...)` (async). Para al recibir `<500` elementos o `[]`.

- [ ] **Step 1: Test que falla**

```python
# tests/test_paginator.py
from ine._paginator import iter_pages


def test_stops_on_short_page():
    pages = {1: list(range(500)), 2: list(range(100))}
    result = list(iter_pages(lambda p: pages[p]))
    assert len(result) == 2
    assert len(result[1]) == 100


def test_stops_on_empty():
    pages = {1: list(range(500)), 2: []}
    result = list(iter_pages(lambda p: pages.get(p, [])))
    assert len(result) == 1  # la página vacía no se yields
```

- [ ] **Step 2: Verificar que falla** — `uv run pytest tests/test_paginator.py -v` → FAIL.

- [ ] **Step 3: Implementar**

```python
# ine/_paginator.py
from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Iterator

PAGE_SIZE = 500


def iter_pages(fetch_page: Callable[[int], list]) -> Iterator[list]:
    page = 1
    while True:
        chunk = fetch_page(page)
        if not chunk:
            return
        yield chunk
        if len(chunk) < PAGE_SIZE:
            return
        page += 1


async def aiter_pages(fetch_page) -> AsyncIterator[list]:
    page = 1
    while True:
        chunk = await fetch_page(page)
        if not chunk:
            return
        yield chunk
        if len(chunk) < PAGE_SIZE:
            return
        page += 1
```

- [ ] **Step 4: Verificar que pasa** — `uv run pytest tests/test_paginator.py -v` → PASS.

- [ ] **Step 5: Commit**

```bash
git add ine/_paginator.py tests/test_paginator.py
git commit -m "feat(paginator): iterador perezoso (stop en <500)"
```

---

### Task 5.3: Builder tipado del filtro `g` (OR/AND anidados)

**Files:**
- Create: `ine/_filters.py`
- Test: `tests/test_filters.py`

**Interfaces:** Produce `FiltroGrupo` y `g` helpers. El param `g` del INE: `g1=["115:29","115:30"]` (OR dentro del grupo), `g2="3:84"` (AND entre grupos).

- [ ] **Step 1: Test que falla**

```python
# tests/test_filters.py
from ine._filters import compilar_filtros


def test_single_group_or():
    # un grupo con 2 condiciones -> g1 con lista (OR)
    out = compilar_filtros([("115", ["29", "30"])])
    assert out == {"g1": ["115:29", "115:30"]}


def test_multiple_groups_and():
    out = compilar_filtros([("115", ["29", "30"]), ("3", ["84"])])
    assert out == {"g1": ["115:29", "115:30"], "g2": "3:84"}


def test_no_value_means_all():
    out = compilar_filtros([("762", None)])
    assert out == {"g1": "762:"}
```

- [ ] **Step 2: Verificar que falla** — `uv run pytest tests/test_filters.py -v` → FAIL.

- [ ] **Step 3: Implementar**

```python
# ine/_filters.py
from __future__ import annotations

Grupo = tuple[str, list[str] | None]


def compilar_filtros(grupos: list[Grupo]) -> dict[str, object]:
    """Compila grupos (var, valores) al param `g` del INE.

    - Múltiples valores en un grupo -> OR (lista).
    - Grupos distintos -> AND.
    - valores=None -> esa variable sin valor (devuelve todos sus valores).
    """
    out: dict[str, object] = {}
    for i, (var, valores) in enumerate(grupos, start=1):
        if valores is None:
            out[f"g{i}"] = f"{var}:"
        elif len(valores) == 1:
            out[f"g{i}"] = f"{var}:{valores[0]}"
        else:
            out[f"g{i}"] = [f"{var}:{v}" for v in valores]
    return out
```

- [ ] **Step 4: Verificar que pasa** — `uv run pytest tests/test_filters.py -v` → PASS.

- [ ] **Step 5: Commit**

```bash
git add ine/_filters.py tests/test_filters.py
git commit -m "feat(filters): builder tipado del param g (OR/AND anidados)"
```

---

### Task 5.4: Catálogo de endpoints — Servicios por dominio

> Cada subtask añade UN dominio como servicio (patrón idéntico al de `Client` pero aislado). Para cada endpoint se da: **path builder, params (con tipo), schema de retorno, paginación (Sí/No), notas**. La implementación sigue el patrón de la Fase 3 (`backend.get(path, params=build_params(...))` + `model_validate` + `raw=True`).
>
> **Regla por endpoint** (aplicar a todos): firma con `*, raw: bool = False`, validar con el modelo indicado, propagar params `None` vía `build_params`.

#### Subtask 5.4.1 — Dominio OPERACIONES (2 spec)

| Método | Path | Params | Retorna | Pagina |
|---|---|---|---|---|
| `operaciones()` | `/OPERACIONES_DISPONIBLES` | `det:Literal["0","1","2"]\|None`, `geo:Literal["0","1"]\|None`, `page:int\|None` | `list[Operacion]` | Sí |
| `operacion(id: str)` | `/OPERACION/{id}` | `det` | `list[Operacion]` | No |

**Notas:** `id` puede ser `Id` numérico, `Codigo` alfabético o `IOEXXXX`. Documentar que `Codigo` **no es único** (H6). Modelo: `Operacion` (Task 3.2).

- [ ] Implementar `ine/services/operaciones.py` + `OperacionesService(backend, config)`; test con 2 endpoints mockeados. Commit `feat(operaciones): servicio con 2 endpoints (paginado)`.

#### Subtask 5.4.2 — Dominio SERIES (5 spec)

| Método | Path | Params | Retorna | Pagina |
|---|---|---|---|---|
| `serie(id_serie)` | `/SERIE/{IdSERIE}` | `det`, `tip:Literal["A","M","AM"]\|None` | `list[Serie]` | No |
| `series_operacion(op)` | `/SERIES_OPERACION/{op}` | `det`, `tip`, `page` | `list[Serie]` | Sí |
| `series_tabla(id_tabla)` | `/SERIES_TABLA/{id_tabla}` | `det`, `tip`, `tv:list[str]\|None` | `list[Serie]` | No |
| `valores_serie(id_serie)` | `/VALORES_SERIE/{IdSERIE}` | `det` | `list[Valor]` | No |
| `series_metadata_operacion(op, *, p, filtros)` | `/SERIE_METADATAOPERACION/{op}` | `p:Literal["1","3","6","12"]\|None`, `det`, `tip`, `g` (vía `compilar_filtros`) | `list[Serie]` | No |

**Modelo `Serie`** (crear `ine/models/series.py`): `id:int|None`, `cod:str|None`, `nombre:str`, `decimales:int`, `fk_operacion:int|None`, `operacion:Operacion|None`, `fk_periodicidad:int|None`, `periodicidad:Periodicidad|None`, `fk_publicacion:int|None`, `fk_clasificacion:int|None`, `fk_escala:int|None`, `escala:Escala|None`, `fk_unidad:int|None`, `unidad:Unidad|None`. (Ver schema `SeriesJSON` del spec; campos `T3_*` omítelos como redundantes —ya están en el FK+objeto— pero `extra="ignore"` los descarta igual.)

- [ ] Implementar `ine/services/series.py` + modelos `Serie`, `Valor`; test; commit.

#### Subtask 5.4.3 — Dominio DATOS (3 spec)

| Método | Path | Params | Retorna | Pagina |
|---|---|---|---|---|
| `datos_serie(id_serie)` | `/DATOS_SERIE/{IdSERIE}` | `nult:int\|None`, `det`, `tip`, `date:list[str]\|None` (formato `aaaammdd:aaaammdd`) | `list[DatosSerie]` | No |
| `datos_tabla(id_tabla)` | `/DATOS_TABLA/{id_tabla}` | `nult`, `det`, `tip`, `tv`, `date` | `list[DatosSerie]` | No |
| `datos_metadataoperacion(op, *, p, nult, det, tip, filtros)` | `/DATOS_METADATAOPERACION/{op}` | `p`, `nult`, `det`, `tip`, `g` | `list[DatosSerie]` | No |

**Modelos:** `DatosSerie` (Task 3.3). El param `date` se pasa como array (httpx serializa múltiples valores).

- [ ] Implementar `ine/services/datos.py`; test; commit.

#### Subtask 5.4.4 — Dominio TABLAS (3 spec)

| Método | Path | Params | Retorna | Pagina |
|---|---|---|---|---|
| `tablas_operacion(op)` | `/TABLAS_OPERACION/{op}` | `det`, `geo`, `tip` | `list[Tabla]` | No |
| `grupos_tabla(id_tabla)` | `/GRUPOS_TABLA/{id_tabla}` | — | `list[Grupo]` | No |
| `valores_grupostabla(id_tabla, id_grupo)` | `/VALORES_GRUPOSTABLA/{id_tabla}/{id_grupo}` | `det` | `list[Valor]` | No |

**Modelo `Tabla`** (`ine/models/tablas.py`): `id:int`, `nombre:str`, `codigo:str|None`, `fk_periodicidad:int|None`, `anyo_periodo_ini:str|None` (¡es string en el spec!), `fecha_ref_fin:str|None`, `ultima_modificacion:datetime|None` (epoch; usar mixin `ConFecha` renombrando campo — valida). `Grupo`: `id:int`, `nombre:str`.

- [ ] Implementar `ine/services/tablas.py` + modelos; test; commit.

#### Subtask 5.4.5 — Dominio VARIABLES (2 spec + 1 no doc)

| Método | Path | Params | Retorna | Pagina | Origen |
|---|---|---|---|---|---|
| `variables()` | `/VARIABLES` | `page` | `list[Variable]` | Sí | spec |
| `variables_operacion(op)` | `/VARIABLES_OPERACION/{op}` | `page` | `list[Variable]` | Sí | spec |
| `variable(id_variable: int)` | `/VARIABLE/{id_variable}` | — | `Variable` | No | **no doc** |

**Modelo `Variable`:** `id:int`, `nombre:str`, `codigo:str|None`.

- [ ] Implementar `ine/services/variables.py`; test; commit.

#### Subtask 5.4.6 — Dominio VALORES (3 spec)

| Método | Path | Params | Retorna | Pagina |
|---|---|---|---|---|
| `valores_variable(id_variable)` | `/VALORES_VARIABLE/{id_variable}` | `det`, `clasif:int\|None` | `list[Valor]` | No |
| `valores_variable_operacion(id_variable, op)` | `/VALORES_VARIABLEOPERACION/{id_variable}/{op}` | `det` | `list[Valor]` | No |
| `valores_hijos(id_variable, id_valor)` | `/VALORES_HIJOS/{id_variable}/{id_valor}` | `det` | `list[Valor]` | No |

**Modelo `Valor`** (`ine/models/valores.py`): `id:int|None`, `nombre:str`, `codigo:str|None`, `fk_variable:int|None`, `t3_variable:str|None`, `variable:list[Variable] = []`.

- [ ] Implementar `ine/services/valores.py`; test; commit.

#### Subtask 5.4.7 — Dominio MAESTROS (no documentados + CLASIFICACIONES/PERIODICIDADES spec)

> Este es el dominio **descubierto empíricamente**. Endpoints que el spec NO documenta pero la API sirve (H1-confirmados con datos reales).

| Método | Path | Params | Retorna | Origen |
|---|---|---|---|---|
| `escalas()` | `/ESCALAS` | — | `list[Escala]` | **no doc** |
| `escala(id: int)` | `/ESCALA/{id}` | — | `Escala` | **no doc** |
| `unidades()` | `/UNIDADES` | — | `list[Unidad]` | **no doc** |
| `unidad(id: int)` | `/UNIDAD/{id}` | — | `Unidad` | **no doc** |
| `unidades_operacion(op)` | `/UNIDADES_OPERACION/{op}` | — | `list[Unidad]` | **no doc** |
| `periodo(id: int)` | `/PERIODO/{id}` | — | `Periodo` | **no doc** (schema más rico: `Valor`, `FK_Periodicidad`, `Dia_inicio`, `Mes_inicio`) |
| `periodicidades()` | `/PERIODICIDADES` | — | `list[Periodicidad]` | spec |
| `periodicidad(id: int)` | `/PERIODICIDAD/{id}` | — | `Periodicidad` | **no doc** |
| `clasificaciones()` | `/CLASIFICACIONES` | — | `list[Clasificacion]` | spec |
| `clasificaciones_operacion(op)` | `/CLASIFICACIONES_OPERACION/{op}` | — | `list[Clasificacion]` | spec |

**Modelos** (`ine/models/maestros.py`):
- `Escala`: `id:int|None`, `nombre:str`, `factor:str|None`, `codigo:str|None`, `abrev:str|None`.
- `Unidad`: `id:int|None`, `nombre:str`, `codigo:str|None`, `abrev:str|None`.
- `Periodicidad`: `id:int|None`, `nombre:str`, `codigo:str|None`.
- `Periodo`: `id:int|None`, `valor:int|None`, `fk_periodicidad:int|None`, `dia_inicio:str|None`, `mes_inicio:str|None`, `codigo:str|None`, `nombre:str|None`, `nombre_largo:str|None`.
- `Clasificacion`: `id:int|None`, `nombre:str`, `fecha:datetime|None` (epoch; mixin).

- [ ] Implementar `ine/services/maestros.py` + modelos; test (con respuestas capturadas de los no-doc); commit. **Etiqueta en docstrings** los endpoints no documentados con `# NO DOCUMENTADO en OpenAPI`.

#### Subtask 5.4.8 — Dominio PUBLICACIONES (3 spec)

| Método | Path | Params | Retorna | Pagina |
|---|---|---|---|---|
| `publicaciones()` | `/PUBLICACIONES` | `det`, `tip` | `list[Publicacion]` | No |
| `publicaciones_operacion(op)` | `/PUBLICACIONES_OPERACION/{op}` | `det`, `tip` | `list[Publicacion]` | No |
| `publicacion_fecha(id_publicacion: int)` | `/PUBLICACIONFECHA_PUBLICACION/{id_publicacion}` | `det`, `tip` | `list[PublicacionFecha]` | No |

**Modelo `Publicacion`:** `id:int|None`, `nombre:str`, `url:str|None`, `fk_periodicidad:int|None`, `periodicidad:list[Periodicidad]=[]`, `fk_pub_fecha_act:int|None`.
**Modelo `PublicacionFecha`** (con `ConFecha`): `id:int|None`, `nombre:str|None`, `fecha:datetime|None`, `anyo:int|None`, `fk_publicacion:int|None`, `fk_periodo:int|None`.

- [ ] Implementar `ine/services/publicaciones.py` + modelos; test; commit.

---

# FASE 6 — Refactor a namespaces + limpieza

> Objetivo: con >10 métodos por `Client`, exponerlos como `client.operaciones`, `client.series`, etc.

### Task 6.1: `Client` con namespaces

**Files:**
- Modify: `ine/client.py`, `ine/async_client.py`
- Create: `ine/services/_base.py` (`BaseService(backend, config)`)
- Delete: `ine/main.py` (y actualizar `hello.py`)

**Cambio de API (rompe compatibilidad, todavía en 0.x — documentar):**

```python
# antes
client.get_operaciones()
client.get_datos_tabla("24077")

# después
client.operaciones.list()
client.datos.tabla("24077")
```

- [ ] **Step 1:** Crear `ine/services/_base.py` con `BaseService` que recibe `backend` y `config` y expone `lang()` (`config.lang.value`) y `_get(path, params)` wrapper.
- [ ] **Step 2:** Mover cada dominio (Fase 5) a heredar de `BaseService`.
- [ ] **Step 3:** En `Client.__init__`, instanciar `self.operaciones = OperacionesService(...)`, `self.series = SeriesService(...)`, etc., como propiedades.
- [ ] **Step 4:** Hacer lo mismo en `AsyncClient` (con un `AsyncBaseService`).
- [ ] **Step 5:** Tests de integración que usen la nueva API de namespaces.
- [ ] **Step 6:** Eliminar `ine/main.py` y actualizar `hello.py`:

```python
# hello.py
from ine import Client

with Client() as client:
    operaciones = client.operaciones.list()
    print(operaciones)
```

- [ ] **Step 7:** Commit `refactor: namespaces por dominio en Client/AsyncClient`.

---

# FASE 7 — Extras opcionales (futuras)

- **`ine-api[dataframe]`:** extra opcional (`uv add --optional dataframe pandas`) con método `.to_dataframe()` en modelos de datos. Mantener fuera del core.
- **Caché explícita opt-in:** decorador/param `cache=` (TTL). Nunca transparente por defecto.
- **CLI:** `ine operaciones list`, `ine datos tabla 24077 --nult 12` (usa `typer`).
- **README completo** con quickstart, tabla de cobertura de endpoints, nota de licencia CC BY 4.0.
- **Soporte de proxy/HTTP/2:** ya cubierto por DI de `httpx_client`; documentarlo.

---

# Criterios de aceptación globales

1. **Cobertura:** los 33 endpoints (24 spec + 9 no doc) tienen método en el cliente + test de contrato.
2. **Robustez H1/H2/H3:** los 3 comportamientos raros tienen tests dedicados en `tests/test_backend.py`.
3. **Sin fuga de recursos:** `Client` y `AsyncClient` son context managers y cierran su `httpx.Client`.
4. **Sin `httpx` en la API pública:** `from ine import Client, AsyncClient` no requiere que el usuario importe `httpx`; las excepciones son de `ine.errors`.
5. **Modelos pydantic:** todas las respuestas tipables se modelan; `raw=True` disponible; `Fecha` es `datetime`; `extra="ignore"`.
6. **Paginación:** los 4 listados paginados ofrecen iteración perezosa completa.
7. **Tooling verde:** `uv run ruff check .`, `uv run mypy ine`, `uv run pytest` todos limpios.
8. **README** documenta la nota de CC BY 4.0 y que `Codigo` no es único.
