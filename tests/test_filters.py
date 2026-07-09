# tests/test_filters.py
from ine._filters import compilar_filtros


def test_single_group_or():
    # un grupo con 2 condiciones -> g1 con lista (OR)
    out = compilar_filtros([("115", ["29", "30"])])
    assert out == {"g1": ["115:29", "115:30"]}


def test_multiple_groups_and():
    out = compilar_filtros([("115", ["29", "30"]), ("3", ["84"])])
    assert out == {"g1": ["115:29", "115:30"], "g2": "3:84"}


def test_no_value_means_all():
    out = compilar_filtros([("762", None)])
    assert out == {"g1": "762:"}
