import requests

from backend.app.open_meteo import ClienteOpenMeteo, ErrorOpenMeteo, nivel_simple


class Respuesta:
    def __init__(self, cuerpo, status=200):
        self.status_code = status
        self._cuerpo = cuerpo

    def json(self):
        if isinstance(self._cuerpo, Exception):
            raise self._cuerpo
        return self._cuerpo


class Sesion:
    def __init__(self, cuerpo, status=200, error=None):
        self.cuerpo = cuerpo
        self.status = status
        self.error = error
        self.llamadas = []

    def get(self, url, params=None, timeout=None):
        self.llamadas.append(url)
        if self.error:
            raise self.error
        return Respuesta(self.cuerpo, self.status)


def test_niveles_siguen_los_cortes_epa():
    assert nivel_simple(50)[0] == "bien"
    assert nivel_simple(51)[0] == "regular"
    assert nivel_simple(100)[0] == "regular"
    assert nivel_simple(101)[0] == "mal"
    assert nivel_simple(301)[2] == "Peligrosa"


def test_cliente_lee_us_aqi_de_medellin():
    sesion = Sesion(
        {
            "current": {
                "us_aqi": 42.2,
                "pm2_5": 8.1,
                "pm10": 15,
                "time": "2026-11-11T16:00",
            }
        }
    )
    datos = ClienteOpenMeteo(sesion=sesion).calidad("Medellín")

    assert datos["us_aqi"] == 42
    assert datos["nivel"] == "bien"
    assert datos["titulo"] == "Bien"
    assert datos["categoria_epa"] == "Buena"
    assert datos["pm2_5"] == 8.1
    assert datos["fuente"] == "Open-Meteo"
    assert "alerta oficial" in datos["aviso"]
    assert sesion.llamadas == [
        "https://air-quality-api.open-meteo.com/v1/air-quality"
    ]


def test_indice_alto_queda_mal():
    sesion = Sesion({"current": {"us_aqi": 160, "pm2_5": 70, "pm10": 90, "time": "t"}})
    datos = ClienteOpenMeteo(sesion=sesion).calidad("Cali")
    assert datos["nivel"] == "mal"
    assert datos["categoria_epa"] == "Dañina"


def test_fallo_de_red_no_inventa_indice():
    sesion = Sesion({}, error=requests.Timeout("lento"))
    try:
        ClienteOpenMeteo(sesion=sesion).calidad("Bogota")
    except ErrorOpenMeteo:
        return
    raise AssertionError("debio fallar")
