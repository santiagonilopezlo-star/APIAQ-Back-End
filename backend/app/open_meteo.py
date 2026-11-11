"""Calidad del aire por ciudad con Open-Meteo.

El índice us_aqi sale del modelo CAMS. No es una medición de estación
ni una alerta oficial. No pide clave.
"""

import unicodedata

import requests

from backend.app.aqi import categoria_aqi

URL_AIRE = "https://air-quality-api.open-meteo.com/v1/air-quality"
URL_GEO = "https://geocoding-api.open-meteo.com/v1/search"
TIEMPO_ESPERA = 10

# Centros urbanos del menú. Evita fallar si el geocoder no reconoce el nombre.
COORDENADAS = {
    "bogota": (4.7110, -74.0721),
    "medellin": (6.2442, -75.5812),
    "cali": (3.4516, -76.5320),
    "barranquilla": (10.9685, -74.7813),
    "cartagena": (10.3910, -75.4794),
    "bucaramanga": (7.1193, -73.1227),
    "pereira": (4.8133, -75.6961),
    "cucuta": (7.8939, -72.5078),
    "santa marta": (11.2408, -74.1990),
    "manizales": (5.0703, -75.5138),
}


class ErrorOpenMeteo(Exception):
    """Open-Meteo no entregó un índice usable."""


def quitar_tildes(texto):
    base = unicodedata.normalize("NFD", str(texto).strip().lower())
    return "".join(letra for letra in base if unicodedata.category(letra) != "Mn")


def nivel_simple(indice):
    """Traduce el US AQI a bien, regular o mal. El nombre EPA va aparte."""
    categoria = categoria_aqi(indice)
    if categoria == "Buena":
        return "bien", "Bien", categoria
    if categoria == "Moderada":
        return "regular", "Regular", categoria
    return "mal", "Mal", categoria


class ClienteOpenMeteo:
    def __init__(self, timeout=TIEMPO_ESPERA, sesion=None):
        self.timeout = timeout
        self.sesion = sesion or requests.Session()

    def calidad(self, ciudad):
        latitud, longitud = self._coordenadas(ciudad)
        datos = self._get(
            URL_AIRE,
            {
                "latitude": latitud,
                "longitude": longitud,
                "current": "us_aqi,pm2_5,pm10",
                "timezone": "UTC",
            },
        )
        actual = datos.get("current") or {}
        crudo = actual.get("us_aqi")
        try:
            indice = int(round(float(crudo)))
        except (TypeError, ValueError) as error:
            raise ErrorOpenMeteo("sin indice") from error
        if indice < 0:
            raise ErrorOpenMeteo("indice invalido")

        nivel, titulo, categoria = nivel_simple(indice)
        return {
            "nivel": nivel,
            "titulo": titulo,
            "us_aqi": indice,
            "categoria_epa": categoria,
            "pm2_5": actual.get("pm2_5"),
            "pm10": actual.get("pm10"),
            "unidad": "µg/m³",
            "fecha": actual.get("time"),
            "fuente": "Open-Meteo",
            "modelo": "CAMS",
            "latitud": latitud,
            "longitud": longitud,
            "aviso": (
                "Estimación del modelo CAMS para la ciudad. "
                "No es una medición de estación ni una alerta oficial."
            ),
        }

    def _coordenadas(self, ciudad):
        clave = quitar_tildes(ciudad)
        if clave in COORDENADAS:
            return COORDENADAS[clave]
        datos = self._get(
            URL_GEO,
            {"name": ciudad, "count": 1, "language": "es", "countryCode": "CO"},
        )
        resultados = datos.get("results") or []
        if not resultados:
            raise ErrorOpenMeteo("sin coordenadas")
        primero = resultados[0]
        return primero.get("latitude"), primero.get("longitude")

    def _get(self, url, params):
        try:
            respuesta = self.sesion.get(url, params=params, timeout=self.timeout)
        except requests.Timeout as error:
            raise ErrorOpenMeteo("tiempo") from error
        except requests.RequestException as error:
            raise ErrorOpenMeteo("red") from error
        if respuesta.status_code != 200:
            raise ErrorOpenMeteo("estado")
        try:
            return respuesta.json()
        except ValueError as error:
            raise ErrorOpenMeteo("json") from error
