import json
from pathlib import Path

import pytest
import requests

from backend.app.cliente_openaq import ClienteOpenAQ, ErrorOpenAQ

DATOS = Path(__file__).parent / "datos"
CLAVE = "clave-de-prueba"


class RespuestaFalsa:
    def __init__(self, status_code=200, payload=None, json_invalido=False):
        self.status_code = status_code
        self.payload = payload
        self.json_invalido = json_invalido

    def json(self):
        if self.json_invalido:
            raise ValueError("no es json")
        return self.payload


class SesionFalsa:
    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []

    def get(self, url, headers=None, params=None, timeout=None):
        self.llamadas.append(
            {"url": url, "headers": headers, "params": params, "timeout": timeout}
        )
        siguiente = self.respuestas.pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return siguiente


def cargar(nombre):
    return json.loads((DATOS / nombre).read_text(encoding="utf-8"))


def test_envia_clave_y_tiempo_de_espera():
    sesion = SesionFalsa([RespuestaFalsa(payload=cargar("pagina_1.json"))])
    cliente = ClienteOpenAQ(api_key=CLAVE, timeout=4, sesion=sesion)

    cliente.obtener("/locations", {"iso": "CO"})

    llamada = sesion.llamadas[0]
    assert llamada["headers"]["X-API-Key"] == CLAVE
    assert llamada["timeout"] == 4
    assert llamada["url"] == "https://api.openaq.org/v3/locations"


def test_sin_clave_no_llama_a_la_red():
    sesion = SesionFalsa([])
    cliente = ClienteOpenAQ(api_key="", sesion=sesion)

    with pytest.raises(ErrorOpenAQ):
        cliente.obtener("/locations")

    assert sesion.llamadas == []


def test_paginacion_une_las_paginas():
    sesion = SesionFalsa(
        [
            RespuestaFalsa(payload=cargar("pagina_1.json")),
            RespuestaFalsa(payload=cargar("pagina_2.json")),
        ]
    )
    cliente = ClienteOpenAQ(api_key=CLAVE, sesion=sesion)

    lugares = cliente.obtener_todo("/locations", {"iso": "CO", "limit": 1})

    assert [lugar["id"] for lugar in lugares] == [10, 11]
    assert sesion.llamadas[0]["params"]["page"] == 1
    assert sesion.llamadas[1]["params"]["page"] == 2
    assert sesion.llamadas[0]["params"]["iso"] == "CO"
    assert sesion.llamadas[0]["params"]["limit"] == 1


def test_buscar_ubicaciones_pide_colombia():
    sesion = SesionFalsa([RespuestaFalsa(payload=cargar("pagina_2.json"))])
    cliente = ClienteOpenAQ(api_key=CLAVE, sesion=sesion)

    lugares = cliente.buscar_ubicaciones()

    assert lugares[0]["locality"] == "Medellín"
    assert sesion.llamadas[0]["params"]["iso"] == "CO"


def test_no_pasa_del_tope_de_paginas():
    pagina_llena = {
        "meta": {"found": 999},
        "results": [{"id": n} for n in range(100)],
    }
    sesion = SesionFalsa([RespuestaFalsa(payload=pagina_llena) for _ in range(6)])
    cliente = ClienteOpenAQ(api_key=CLAVE, sesion=sesion)

    lugares = cliente.obtener_todo("/locations", {"iso": "CO"})

    assert len(sesion.llamadas) == 5
    assert len(lugares) == 500


def test_timeout_se_convierte_en_error():
    sesion = SesionFalsa([requests.Timeout("lento")])
    cliente = ClienteOpenAQ(api_key=CLAVE, sesion=sesion)

    with pytest.raises(ErrorOpenAQ, match="Tiempo de espera"):
        cliente.obtener("/locations")


def test_limite_de_solicitudes_no_reintenta():
    sesion = SesionFalsa([RespuestaFalsa(status_code=429, payload={"results": []})])
    cliente = ClienteOpenAQ(api_key=CLAVE, sesion=sesion)

    with pytest.raises(ErrorOpenAQ, match="no está disponible") as info:
        cliente.obtener("/locations")

    assert len(sesion.llamadas) == 1
    assert CLAVE not in str(info.value)


def test_error_del_servidor():
    sesion = SesionFalsa([RespuestaFalsa(status_code=503, payload={"results": []})])
    cliente = ClienteOpenAQ(api_key=CLAVE, sesion=sesion)

    with pytest.raises(ErrorOpenAQ):
        cliente.obtener("/locations")


def test_json_invalido():
    sesion = SesionFalsa([RespuestaFalsa(json_invalido=True)])
    cliente = ClienteOpenAQ(api_key=CLAVE, sesion=sesion)

    with pytest.raises(ErrorOpenAQ, match="JSON"):
        cliente.obtener("/locations")


def test_respuesta_sin_results():
    sesion = SesionFalsa([RespuestaFalsa(payload={"meta": {}})])
    cliente = ClienteOpenAQ(api_key=CLAVE, sesion=sesion)

    with pytest.raises(ErrorOpenAQ, match="formato"):
        cliente.obtener("/locations")
