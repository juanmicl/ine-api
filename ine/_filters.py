# ine/_filters.py
"""Builder tipado del query param ``g`` del INE.

Los endpoints ``DATOS_METADATAOPERACION`` / ``SERIE_METADATAOPERACION`` aceptan
un parámetro ``g`` con una sintaxis especial que permite combinar filtros:

- ``g1=["115:29", "115:30"]`` — varias condiciones para la *misma* variable
  se interpretan como OR dentro del grupo.
- ``g2="3:84"`` — grupos distintos (``g1``, ``g2``, ...) se combinan con AND.
- ``g3="762:"`` — variable sin valor concreto: devuelve todos los valores
  posibles de esa variable (útil para forzar su presencia en la respuesta).

Este módulo es una utilidad pura: no realiza HTTP. Compila una lista de grupos
``[(var, [valores])]`` al ``dict`` que se envía como ``params`` del INE.
"""

from __future__ import annotations

#: Un grupo de filtro: la variable y, opcionalmente, la lista de valores.
#: ``valores=None`` significa "todos los valores de esa variable".
Grupo = tuple[str, list[str] | None]


def compilar_filtros(grupos: list[Grupo]) -> dict[str, object]:
    """Compila grupos ``(var, valores)`` al param ``g`` del INE.

    Cada grupo genera una clave ``g1``, ``g2``, ... (en orden de aparición):

    - Múltiples valores en un grupo -> OR (lista tipo ``["var:v1", "var:v2"]``).
    - Un único valor -> cadena ``"var:v1"``.
    - ``valores`` es ``None`` -> ``"var:"`` (todos los valores de esa variable).

    Los grupos distintos se combinan con AND (son claves ``g`` distintas).
    """
    out: dict[str, object] = {}
    for i, (var, valores) in enumerate(grupos, start=1):
        if valores is None:
            out[f"g{i}"] = f"{var}:"
        elif len(valores) == 1:
            out[f"g{i}"] = f"{var}:{valores[0]}"
        else:
            out[f"g{i}"] = [f"{var}:{v}" for v in valores]
    return out
