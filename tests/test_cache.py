import pytest

from ine._cache import Cache


def test_miss_returns_none():
    cache = Cache()
    assert cache.get("missing") is None


def test_set_then_get_hits():
    cache = Cache()
    cache.set("k", {"data": 1})
    assert cache.get("k") == {"data": 1}


def test_ttl_expiry(monkeypatch):
    t = [0.0]
    monkeypatch.setattr("ine._cache._now", lambda: t[0])

    cache = Cache(ttl=10.0)
    t[0] = 100.0
    cache.set("k", "v")
    assert cache.get("k") == "v"  # fresco

    # Límite exacto: _now() >= expiry  →  expira
    t[0] = 110.0
    assert cache.get("k") is None
    assert len(cache) == 0  # purgado


def test_ttl_just_before_expiry_is_fresh(monkeypatch):
    t = [0.0]
    monkeypatch.setattr("ine._cache._now", lambda: t[0])

    cache = Cache(ttl=10.0)
    t[0] = 100.0
    cache.set("k", "v")

    t[0] = 109.999  # estrictamente menor que expiry (110)
    assert cache.get("k") == "v"


def test_clear_empties():
    cache = Cache()
    cache.set("a", 1)
    cache.set("b", 2)
    assert len(cache) == 2
    cache.clear()
    assert len(cache) == 0
    assert cache.get("a") is None


def test_maxsize_fifo_eviction():
    cache = Cache(ttl=300, maxsize=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)  # excede maxsize → evicta el más antiguo ("a")
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3


def test_len_and_contains():
    cache = Cache()
    assert "k" not in cache
    assert len(cache) == 0
    cache.set("k", 1)
    assert "k" in cache
    assert len(cache) == 1


def test_contains_false_when_expired(monkeypatch):
    t = [0.0]
    monkeypatch.setattr("ine._cache._now", lambda: t[0])

    cache = Cache(ttl=5.0)
    t[0] = 0.0
    cache.set("k", 1)
    assert "k" in cache

    t[0] = 6.0
    assert "k" not in cache  # expirado (y __contains__ pasa por get → purga)


@pytest.mark.parametrize("ttl", [-1, -0.5])
def test_invalid_ttl_raises(ttl):
    with pytest.raises(ValueError):
        Cache(ttl=ttl)


@pytest.mark.parametrize("maxsize", [0, -1, -5])
def test_invalid_maxsize_raises(maxsize):
    with pytest.raises(ValueError):
        Cache(maxsize=maxsize)


def test_overwrite_updates_value():
    cache = Cache()
    cache.set("k", 1)
    cache.set("k", 2)  # sobreescribe sin duplicar
    assert cache.get("k") == 2
    assert len(cache) == 1


def test_overwrite_refreshes_fifo_position():
    cache = Cache(ttl=300, maxsize=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("a", 1)  # reinserta "a" al final → "b" queda como más antiguo
    cache.set("c", 3)  # evicta "b"
    assert cache.get("a") == 1
    assert cache.get("b") is None
    assert cache.get("c") == 3


def test_defaults():
    cache = Cache()
    assert len(cache) == 0
    cache.set("k", 1)
    # ttl por defecto (300s) → no expira a corto plazo
    assert "k" in cache


def test_none_is_a_valid_value():
    cache = Cache()
    cache.set("k", None)
    # None como dato es indistinguible de miss por diseño (get -> None).
    assert cache.get("k") is None
    assert "k" not in cache
    assert len(cache) == 1  # sigue ocupando sitio hasta expirar
