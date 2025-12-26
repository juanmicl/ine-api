import httpx


class Client:
    def __init__(self):
        self.client = httpx.Client(base_url="https://servicios.ine.es")
        self.lang = "ES"

    def _get(self, path):
        response = self.client.get(path)
        return response.json()

    def get_operaciones(self):
        return self._get(f"/wstempus/js/{self.lang}/OPERACIONES_DISPONIBLES")

    def get_tablas(self, operacion):
        return self._get(f"/wstempus/js/{self.lang}/TABLAS_OPERACION/{operacion}")

    def get_datos_tabla(self, tabla_id):
        return self._get(f"/wstempus/js/{self.lang}/DATOS_TABLA/{tabla_id}")
