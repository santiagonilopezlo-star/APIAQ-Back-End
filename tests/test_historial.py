from pathlib import Path

from backend.app.almacen import Almacen
from backend.app.cliente_openaq import ErrorOpenAQ
from backend.app.main import crear_app


def medicion(estacion="10", contaminante="pm25", valor=12.5, fecha="2024-09-05T16:00:00Z"):
    return {
        "estacion_id": estacion,
        "contaminante": contaminante,
        "valor": valor,
        "unidad": "µg/m³",
        "periodo": "1h",
        "fecha_medicion": fecha,
        "fuente": "OpenAQ",
    }


def test_deduplicacion_y_orden_cronologico(tmp_path):
    db = tmp_path / "t.db"
    almacen = Almacen(ruta_db=db)
    m1 = medicion(fecha="2024-09-01T10:00:00Z", valor=10)
    m2 = medicion(fecha="2024-09-05T16:00:00Z", valor=20)
    almacen.guardar_consulta_ok("Medellin", "2026-11-03T12:00:00Z", "OpenAQ", [m1, m2])
    almacen.guardar_consulta_ok("Medellin", "2026-11-03T13:00:00Z", "OpenAQ", [m2])

    mediciones = almacen.listar_mediciones()
    consultas = almacen.listar_consultas()

    assert len(mediciones) == 2
    assert mediciones[0]["fecha_medicion"] < mediciones[1]["fecha_medicion"]
    assert mediciones[0]["fecha_medicion"].endswith("Z")
    assert consultas[0]["fecha_consulta"] == "2026-11-03T13:00:00Z"
    assert consultas[1]["fecha_consulta"] == "2026-11-03T12:00:00Z"


def test_filtros_estacion_contaminante_y_rango_vacio(tmp_path):
    almacen = Almacen(ruta_db=tmp_path / "f.db")
    almacen.guardar_consulta_ok(
        "Medellin",
        "2026-11-03T12:00:00Z",
        "OpenAQ",
        [
            medicion("10", "pm25", 12, "2024-09-01T00:00:00Z"),
            medicion("10", "no2", 8, "2024-09-02T00:00:00Z"),
            medicion("11", "pm25", 9, "2024-09-03T00:00:00Z"),
        ],
    )

    solo_pm25 = almacen.listar_mediciones(contaminante="pm25")
    solo_10 = almacen.listar_mediciones(estacion_id="10")
    rango = almacen.listar_mediciones(desde="2024-09-02T00:00:00Z", hasta="2024-09-02T23:59:59Z")
    vacio = almacen.listar_mediciones(desde="2030-01-01T00:00:00Z", hasta="2030-01-02T00:00:00Z")

    assert len(solo_pm25) == 2
    assert len(solo_10) == 2
    assert len(rango) == 1
    assert rango[0]["contaminante"] == "no2"
    assert vacio == []


def test_endpoints_historial(tmp_path):
    class ClienteVacio:
        def buscar_ubicaciones(self, iso="CO"):
            return []

    app = crear_app(cliente=ClienteVacio(), ruta_db=tmp_path / "api.db")
    cliente = app.test_client()
    almacen = app.almacen
    almacen.guardar_consulta_ok(
        "Medellin",
        "2026-11-03T12:00:00Z",
        "OpenAQ",
        [medicion(fecha="2024-09-05T16:00:00Z")],
    )

    historial = cliente.get("/historial")
    assert historial.status_code == 200
    assert historial.get_json()[0]["ciudad"] == "Medellin"

    mediciones = cliente.get(
        "/historial/mediciones?estacion_id=10&contaminante=pm25"
        "&desde=2024-09-01T00:00:00Z&hasta=2024-09-06T00:00:00Z"
    )
    assert mediciones.status_code == 200
    assert mediciones.get_json()[0]["valor"] == 12.5

    vacio = cliente.get(
        "/historial/mediciones?desde=2030-01-01T00:00:00Z&hasta=2030-01-02T00:00:00Z"
    )
    assert vacio.get_json() == []

    csv_resp = cliente.get("/historial/descargar")
    assert csv_resp.status_code == 200
    assert "fecha_consulta,ciudad,resultado,fuente" in csv_resp.get_data(as_text=True)


def test_descarga_historial_vacio(tmp_path):
    app = crear_app(ruta_db=tmp_path / "vacio.db").test_client()
    respuesta = app.get("/historial/descargar")
    assert respuesta.status_code == 404
    assert respuesta.get_json()["error"] == "historial_vacio"


def test_error_no_guarda_historial(tmp_path):
    class ClienteMalo:
        def buscar_ubicaciones(self, iso="CO"):
            raise ErrorOpenAQ("fallo")

    app = crear_app(cliente=ClienteMalo(), ruta_db=tmp_path / "err.db")
    respuesta = app.test_client().post("/consultar", json={"ciudad": "Medellin"})
    assert respuesta.status_code == 502
    assert app.almacen.listar_consultas() == []
