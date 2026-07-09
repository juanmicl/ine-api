"""Smoke-test mínimo del cliente ine-api (requiere conexión a internet)."""

from ine import Client

with Client() as client:
    print(client.operaciones.list()[:1])
