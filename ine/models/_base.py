# ine/models/_base.py
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from pydantic.alias_generators import to_snake


class _BaseModel(BaseModel):
    """Base para modelos del INE.

    El INE envía claves en PascalCase irregular (``FK_Periodicidad``,
    ``Cod_IOE``, ``FK_PubFechaAct``, ``Anyo_Periodo_ini``...). Normalizamos las
    CLAVES de entrada con ``to_snake`` (PascalCase→snake es determinista) y
    declaramos los campos en snake_case. ``extra='ignore'`` descarta campos
    desconocidos (el INE añade campos sin avisar; el spec tiene bugs).
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def _normalize_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # ``to_snake`` no es idempotente en snake con dígitos
            # (``t3_operacion`` -> ``t_3_operacion``), así que sólo la aplicamos
            # a claves que aún NO están normalizadas: las PascalCase del INE
            # siempre contienen mayúsculas, las snake son todo minúsculas.
            return {(to_snake(k) if any(c.isupper() for c in k) else k): v for k, v in data.items()}
        return data


class ConFecha(_BaseModel):
    """Mixin para modelos con un campo ``fecha`` que el INE envía como epoch-ms.

    ``check_fields=False`` es necesario porque el mixin no declara ``fecha``;
    lo hacen las subclases concretas.
    """

    @field_validator("fecha", mode="before", check_fields=False)
    @classmethod
    def _epoch_ms(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return datetime.fromtimestamp(v / 1000, tz=UTC)
        return v
