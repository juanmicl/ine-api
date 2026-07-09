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
