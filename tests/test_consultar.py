import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.cliente_openaq import ErrorOpenAQ
from backend.app.main import crear_app

DATOS = Path(__file__).parent / "datos"


def cargar(nombre):
    return json.loads((DATOS / nombre).read_text(encoding="utf-8"))


def fecha_iso(dias):
    momento = datetime.now(timezone.utc) - timedelta(days=dias)
    return momento.strftime("%Y-%m-%dT%H:%M:%SZ")


class ClienteConsulta:
    def __init__(self, lugares, lecturas=None, error=None, explota=False):
        self.lugares = lugares
        self.lecturas = lecturas or {}
        self.error = error
        self.explota = explota

    def buscar_ubicaciones(self, iso="CO"):
        if self.explota:
            raise RuntimeError("boom secreto")
        if self.error:
            raise self.error
        return self.lugares

    def ultima_lectura(self, ubicacion_id):
        if self.error:
            raise self.error
        return self.lecturas.get(ubicacion_id, [])


def cliente_bogota(valor=12.5, dias=1, unidad="µg/m³"):
    lugares = cargar("pagina_1.json")["results"]
    lectura = cargar("latest_centro.json")["results"]
    lectura[0]["value"] = valor
    lectura[0]["datetime"]["utc"] = fecha_iso(dias)
    lugares[0]["sensors"][0]["parameter"]["units"] = unidad
    return ClienteConsulta(lugares, {10: lectura})


def app_cliente(cliente, tmp_path):
    return crear_app(cliente=cliente, ruta_db=tmp_path / "test.db").test_client()


def test_consultar_devuelve_medicion_sin_convertir(tmp_path):
    app = app_cliente(cliente_bogota(), tmp_path)
    respuesta = app.post("/consultar", json={"ciudad": "Bogotá"})
    datos = respuesta.get_json()

    assert respuesta.status_code == 200
    assert datos["ciudad"] == "Bogotá"
    assert datos["fuente"] == "OpenAQ"
    assert datos["mediciones"][0]["contaminante"] == "pm25"
    assert datos["mediciones"][0]["valor"] == 12.5
    assert datos["mediciones"][0]["unidad"] == "µg/m³"
    assert datos["mediciones"][0]["periodo"] == "1h"
    assert datos["mediciones"][0]["estacion_id"] == "10"
    assert datos["aqi_epa"]["indice"] is None
    assert datos["aqi_epa"]["estandar"] == "US EPA AQI"
    assert "compatibles" in datos["aqi_epa"]["motivo"]
    assert datos["referencia_oms"]["estado"] == "dato_insuficiente"
    assert datos["referencia_oms"]["separada_del_aqi"] is True
    assert datos["aqi_epa"] != datos["referencia_oms"]
    assert app.get("/historial").get_json()[0]["resultado"] == "ok"


def test_ciudad_invalida(tmp_path):
    app = app_cliente(ClienteConsulta([]), tmp_path)

    vacia = app.post("/consultar", json={"ciudad": ""})
    numeros = app.post("/consultar", json={"ciudad": "Cali 1"})
    sin_cuerpo = app.post("/consultar", data="hola", content_type="text/plain")

    for respuesta in (vacia, numeros, sin_cuerpo):
        assert respuesta.status_code == 400
        assert respuesta.get_json()["error"] == "ciudad_invalida"


def test_sin_datos_si_no_hay_cobertura(tmp_path):
    sin_ciudad = app_cliente(cliente_bogota(), tmp_path)
    falta = sin_ciudad.post("/consultar", json={"ciudad": "Cali"})

    assert falta.status_code == 404
    assert falta.get_json()["error"] == "sin_datos"
    assert sin_ciudad.get("/historial").get_json() == []


def test_consulta_conserva_medicion_antigua(tmp_path):
    respuesta = app_cliente(cliente_bogota(dias=400), tmp_path).post(
        "/consultar", json={"ciudad": "Bogota"}
    )
    datos = respuesta.get_json()

    assert respuesta.status_code == 200
    assert datos["mediciones"][0]["valor"] == 12.5
    assert datos["mediciones"][0]["fecha_medicion"]


def test_openaq_no_disponible(tmp_path):
    cliente = ClienteConsulta([], error=ErrorOpenAQ("clave-interna"))
    respuesta = app_cliente(cliente, tmp_path).post("/consultar", json={"ciudad": "Cali"})
    texto = respuesta.get_data(as_text=True)

    assert respuesta.status_code == 502
    assert respuesta.get_json()["error"] == "openaq_no_disponible"
    assert "clave-interna" not in texto


def test_error_interno_no_muestra_el_detalle(tmp_path):
    cliente = ClienteConsulta([], explota=True)
    respuesta = app_cliente(cliente, tmp_path).post("/consultar", json={"ciudad": "Cali"})
    texto = respuesta.get_data(as_text=True)

    assert respuesta.status_code == 500
    assert respuesta.get_json()["error"] == "error_interno"
    assert "boom secreto" not in texto
