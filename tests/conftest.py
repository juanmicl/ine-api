# tests/conftest.py
import pytest
import respx


@pytest.fixture
def mock_ine():
    """Fixture que mockingea https://servicios.ine.es para un test."""
    with respx.mock:
        yield respx
