"""Quickstart sincrono del cliente ine-api.

Necesita conexión a internet: consulta la API pública del INE en vivo.

Uso:
    uv run python examples/quickstart_sync.py
"""

from ine import Client, Lang


def main() -> None:
    with Client(lang=Lang.ES) as client:
        # 1) Primeras 5 operaciones estadísticas disponibles (IPC, EPA, ...).
        operaciones = client.operaciones.list()
        print(f"{len(operaciones)} operaciones disponibles. Primeras 5:")
        for op in operaciones[:5]:
            print(f"  id={op.id} codigo={op.codigo!r} nombre={op.nombre}")

        # 2) Últimas observaciones de la serie IPC53262 (IPC general, base 2021).
        #    Se pide la serie completa y nos quedamos con las últimas 12.
        datos = client.datos.serie("53262")
        for serie in datos:
            print(f"\nSerie {serie.cod} — {serie.nombre}:")
            for obs in serie.data[-12:]:
                print(f"  {obs.fecha.isoformat()}  {obs.valor}")


if __name__ == "__main__":
    main()
