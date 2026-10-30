import os

import requests

URL_BASE = "https://api.openaq.org/v3"
TIEMPO_ESPERA = 10
LIMITE_PAGINA = 100
MAX_PAGINAS = 5


class ErrorOpenAQ(Exception):
    """OpenAQ no respondió de una forma que se pueda usar."""


class ClienteOpenAQ:
    """Cliente sencillo de la API v3. La clave sale del entorno o del argumento."""

    def __init__(self, api_key=None, timeout=TIEMPO_ESPERA, sesion=None):
        if api_key is None:
            api_key = os.environ.get("OPENAQ_API_KEY", "")
        self.api_key = (api_key or "").strip()
        self.timeout = timeout
        self.sesion = sesion or requests.Session()

    def _encabezados(self):
        if not self.api_key:
            raise ErrorOpenAQ("Falta la variable OPENAQ_API_KEY")
        return {"X-API-Key": self.api_key, "Accept": "application/json"}

    def obtener(self, ruta, params=None):
        """Hace un GET. Lanza ErrorOpenAQ si hay timeout, límite o JSON inválido."""
        try:
            respuesta = self.sesion.get(
                URL_BASE + ruta,
                headers=self._encabezados(),
                params=dict(params or {}),
                timeout=self.timeout,
            )
        except requests.Timeout as error:
            raise ErrorOpenAQ("Tiempo de espera agotado") from error
        except requests.RequestException as error:
            raise ErrorOpenAQ("No se pudo conectar con OpenAQ") from error

        if respuesta.status_code == 429 or respuesta.status_code >= 500:
            raise ErrorOpenAQ("OpenAQ no está disponible")
        if respuesta.status_code >= 400:
            raise ErrorOpenAQ("OpenAQ rechazó la consulta")

        try:
            datos = respuesta.json()
        except ValueError as error:
            raise ErrorOpenAQ("La respuesta no es JSON válido") from error

        if not isinstance(datos, dict) or not isinstance(datos.get("results"), list):
            raise ErrorOpenAQ("La respuesta no tiene el formato esperado")
        return datos

    def obtener_todo(self, ruta, params=None):
        """Recorre páginas hasta agotar resultados o llegar al tope."""
        consulta = dict(params or {})
        consulta["limit"] = int(consulta.get("limit", LIMITE_PAGINA))
        acumulado = []
        pagina = 1

        while pagina <= MAX_PAGINAS:
            consulta["page"] = pagina
            datos = self.obtener(ruta, consulta)
            resultados = datos["results"]
            acumulado.extend(resultados)

            encontrados = (datos.get("meta") or {}).get("found")
            if not resultados:
                break
            if isinstance(encontrados, int) and len(acumulado) >= encontrados:
                break
            if len(resultados) < consulta["limit"]:
                break
            pagina += 1

        return acumulado

    def buscar_ubicaciones(self, iso="CO"):
        return self.obtener_todo("/locations", {"iso": iso})

    def ultima_lectura(self, ubicacion_id):
        datos = self.obtener(f"/locations/{ubicacion_id}/latest")
        return datos["results"]
