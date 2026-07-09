# ine/__init__.py
"""Cliente Python para la API Tempus del INE."""

from ine import errors as errors
from ine._config import Lang as Lang
from ine.client import Client as Client

__all__ = ["Client", "Lang", "errors"]
