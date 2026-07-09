# tests/test_files.py
import pytest

from ine._files import Format, build_file_url


@pytest.mark.parametrize(
    ("fmt", "segment", "ext"),
    [
        (Format.CSV_BDSC, "csv_bdsc", "csv"),
        (Format.CSV_BD, "csv_bd", "csv"),
        (Format.PX, "px", "px"),
        (Format.XLSX, "xlsx", "xlsx"),
    ],
)
def test_build_file_url_format_segment_and_extension(fmt, segment, ext):
    # Cada Format produce el segmento y la extensión de fichero correctos.
    url = build_file_url("es", fmt, "68535")
    assert url == f"https://www.ine.es/jaxiT3/files/t/es/{segment}/68535.{ext}?nocab=1"


def test_build_file_url_embeds_lang():
    # lang va en el segmento /t/{lang}/...
    assert "/t/en/csv_bdsc/" in build_file_url("en", Format.CSV_BDSC, "1")


def test_build_file_url_has_nocab_query():
    # ?nocab=1 fuerza generación fresca (siempre presente).
    assert build_file_url("es", Format.PX, "1").endswith("?nocab=1")


def test_build_file_url_uses_file_base_host():
    # El servicio de ficheros NO es el host de Tempus JSON.
    assert build_file_url("es", Format.XLSX, "1").startswith("https://www.ine.es/jaxiT3/files")


def test_format_str_enum_values():
    # StrEnum: el valor es el string literal que va en la URL.
    assert Format.CSV_BDSC == "csv_bdsc"
    assert Format.CSV_BD == "csv_bd"
    assert Format.PX == "px"
    assert Format.XLSX == "xlsx"
