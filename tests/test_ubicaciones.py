import json
from pathlib import Path

from backend.app.cliente_openaq import ErrorOpenAQ
from backend.app.main import crear_app

DATOS = Path(__file__).parent / "datos"


def cargar(nombre):
    return json.loads((DATOS / nombre).read_text(encoding="utf-8"))


class ClienteFalso:
    def __init__(self, lugares=None, error=None):
        self.lugares = lugares if lugares is not None else []
        self.error = error
        self.iso = None

    def buscar_ubicaciones(self, iso="CO"):
        self.iso = iso
        if self.error:
            raise self.error
        return self.lugares


def app_cliente(cliente, tmp_path):
    return crear_app(cliente=cliente, ruta_db=tmp_path / "ubi.db").test_client()


def test_ubicaciones_con_resultados(tmp_path):
    lugares = cargar("pagina_1.json")["results"] + cargar("pagina_2.json")["results"]
    cliente = ClienteFalso(lugares)
    respuesta = app_cliente(cliente, tmp_path).get("/ubicaciones?ciudad=Bogota")
    datos = respuesta.get_json()

    assert respuesta.status_code == 200
    assert cliente.iso == "CO"
    assert datos == [
        {
            "id": "10",
            "ciudad": "Bogotá",
            "nombre": "Estacion Centro",
            "fuente": "OpenAQ",
            "latitud": 4.65,
            "longitud": -74.08,
        }
    ]


def test_ubicaciones_sin_cobertura(tmp_path):
    cliente = ClienteFalso(cargar("pagina_1.json")["results"])
    respuesta = app_cliente(cliente, tmp_path).get("/ubicaciones?ciudad=Cali")

    assert respuesta.status_code == 200
    assert respuesta.get_json() == []


def test_busqueda_vacia(tmp_path):
    cliente = ClienteFalso([])
    app = app_cliente(cliente, tmp_path)

    vacia = app.get("/ubicaciones?ciudad=")
    ausente = app.get("/ubicaciones")
    numeros = app.get("/ubicaciones?ciudad=Bogota1")

    for respuesta in (vacia, ausente, numeros):
        assert respuesta.status_code == 400
        assert respuesta.get_json()["error"] == "ciudad_invalida"
    assert cliente.iso is None


def test_openaq_caido_en_ubicaciones(tmp_path):
    cliente = ClienteFalso(error=ErrorOpenAQ("clave-no-mostrar"))
    respuesta = app_cliente(cliente, tmp_path).get("/ubicaciones?ciudad=Medellin")
    cuerpo = respuesta.get_data(as_text=True)

    assert respuesta.status_code == 502
    assert respuesta.get_json()["error"] == "openaq_no_disponible"
    assert "clave-no-mostrar" not in cuerpo
