from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class Lang(StrEnum):
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
