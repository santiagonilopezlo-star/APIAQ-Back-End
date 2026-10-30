import os

from backend.app.main import crear_app


def test_salud_responde_ok(monkeypatch):
    monkeypatch.delenv("OPENAQ_API_KEY", raising=False)
    cliente = crear_app().test_client()

    respuesta = cliente.get("/salud")
    datos = respuesta.get_json()

    assert respuesta.status_code == 200
    assert datos["estado"] == "ok"
    assert datos["servicio"] == "monitor-calidad-aire"
    assert datos["version"] == "0.1.0"
    assert datos["openaq_configurado"] is False


def test_salud_indica_si_hay_clave_sin_mostrarla(monkeypatch):
    monkeypatch.setenv("OPENAQ_API_KEY", "clave-secreta-de-prueba")
    cliente = crear_app().test_client()

    respuesta = cliente.get("/salud")
    texto = respuesta.get_data(as_text=True)

    assert respuesta.get_json()["openaq_configurado"] is True
    assert "clave-secreta-de-prueba" not in texto
    assert os.environ["OPENAQ_API_KEY"] not in texto
