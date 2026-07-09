"""Cliente Python para la API Tempus del INE (Instituto Nacional de Estadística).

Punto de entrada: :class:`~ine.client.Client` (sincrono) y
:class:`~ine.async_client.AsyncClient` (asincrono). Excepciones en
:mod:`ine.errors`.
"""

from ine import errors as errors
from ine._cache import Cache as Cache
from ine._config import Lang as Lang
from ine._config import __version__ as __version__
from ine._files import Format as Format
from ine.async_client import AsyncClient as AsyncClient
from ine.client import Client as Client

__all__ = ["AsyncClient", "Cache", "Client", "Format", "Lang", "__version__", "errors"]
