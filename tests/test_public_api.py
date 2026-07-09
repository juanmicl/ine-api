# tests/test_public_api.py
"""Guard de contrato del API público: evita regresiones en los reexport."""


def test_public_imports():
    from ine import AsyncClient, Client, Lang, errors

    assert Client and AsyncClient and Lang
    assert errors.INEError and errors.INEHTTPError and errors.INENotFoundError
