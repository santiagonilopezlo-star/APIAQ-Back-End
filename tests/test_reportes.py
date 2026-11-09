from backend.app.main import crear_app
from backend.app.reportes import generar_imagen_estadisticas, generar_imagen_historial


def filas():
    return [
        {
            "estacion_id": "10",
            "contaminante": "pm25",
            "valor": 12.5,
            "unidad": "µg/m³",
            "periodo": "1h",
            "fecha_medicion": "2024-09-01T10:00:00Z",
            "fuente": "OpenAQ",
        },
        {
            "estacion_id": "10",
            "contaminante": "pm25",
            "valor": 20.0,
            "unidad": "µg/m³",
            "periodo": "1h",
            "fecha_medicion": "2024-09-05T16:00:00Z",
            "fuente": "OpenAQ",
        },
        {
            "estacion_id": "10",
            "contaminante": "no2",
            "valor": 8.0,
            "unidad": "µg/m³",
            "periodo": "1h",
            "fecha_medicion": "2024-09-05T16:00:00Z",
            "fuente": "OpenAQ",
        },
    ]


def test_genera_png_historial_en_static():
    resultado = generar_imagen_historial(filas(), contaminante="pm25", estacion_id="10")
    assert resultado["estado"] == "ok"
    assert resultado["url"].startswith("/static/graficas/")
    assert resultado["archivo"].endswith(".png")
    from pathlib import Path

    assert Path(resultado["ruta"]).exists()


def test_genera_png_estadisticas():
    resultado = generar_imagen_estadisticas(filas())
    assert resultado["estado"] == "ok"
    assert resultado["tabla"]
    from pathlib import Path

    assert Path(resultado["ruta"]).exists()


def test_endpoint_reportes_usa_almacen(tmp_path):
    app = crear_app(ruta_db=tmp_path / "r.db")
    app.almacen.guardar_consulta_ok(
        "Medellin",
        "2026-11-09T12:00:00Z",
        "OpenAQ",
        filas(),
    )
    cliente = app.test_client()

    grafica = cliente.get("/reportes/grafica?contaminante=pm25")
    stats = cliente.get("/reportes/estadisticas")
    assert grafica.status_code == 200
    assert stats.status_code == 200
    assert grafica.get_json()["url"].endswith(".png")
    assert stats.get_json()["url"].endswith(".png")

    nombre = grafica.get_json()["archivo"]
    imagen = cliente.get(f"/static/graficas/{nombre}")
    assert imagen.status_code == 200
    assert imagen.content_type.startswith("image/")


def test_reportes_vacios(tmp_path):
    cliente = crear_app(ruta_db=tmp_path / "v.db").test_client()
    assert cliente.get("/reportes/grafica?contaminante=pm25").status_code == 404
    assert cliente.get("/reportes/estadisticas").status_code == 404
