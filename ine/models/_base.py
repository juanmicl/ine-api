# ine/models/_base.py
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


def to_ine_alias(field_name: str) -> str:
    """Genera el alias PascalCase del INE desde un nombre de campo snake_case.

    El INE envía campos en PascalCase con prefijos `FK_`/`T3_` en mayúsculas
    (p.ej. `FK_Periodicidad`, `T3_Operacion`) y el resto en PascalCase simple
    (`Fecha`, `Nombre`). Ningún generador estándar de pydantic
    (`to_snake`/`to_pascal`/`to_camel`) reconstruye estos prefijos, por lo que
    aquí derivamos el alias:

      - ``fk_periodicidad`` -> ``FK_Periodicidad``
      - ``t3_operacion``    -> ``T3_Operacion``
      - ``fecha``           -> ``Fecha``
      - ``nombre``          -> ``Nombre``
    """
    if "_" in field_name:
        prefix, rest = field_name.split("_", 1)
        return f"{prefix.upper()}_{rest.capitalize()}"
    return field_name.capitalize()


class _BaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_ine_alias,
        populate_by_name=True,
        extra="ignore",
    )


class ConFecha(_BaseModel):
    """Mixin para modelos con un campo `fecha` (alias `Fecha`) en epoch-ms.

    Hereda y declara `fecha: datetime`. El validator convierte epoch-ms
    (int/float) a datetime UTC antes de la coerción de pydantic.

    `check_fields=False` es necesario porque el mixin no declara `fecha` él
    mismo; lo hacen las subclases concretas.
    """

    @field_validator("fecha", mode="before", check_fields=False)
    @classmethod
    def _epoch_ms(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return datetime.fromtimestamp(v / 1000, tz=UTC)
        return v
