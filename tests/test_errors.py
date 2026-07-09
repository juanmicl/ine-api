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
