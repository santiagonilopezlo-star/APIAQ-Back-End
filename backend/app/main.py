import os
import unicodedata

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from backend.app.cliente_openaq import ClienteOpenAQ, ErrorOpenAQ
from backend.app.errores import respuesta_error

VERSION = "0.1.0"


def quitar_tildes(texto):
    base = unicodedata.normalize("NFD", str(texto).strip().lower())
    return "".join(letra for letra in base if unicodedata.category(letra) != "Mn")


def ciudad_valida(ciudad):
    if ciudad is None:
        return False
    limpio = str(ciudad).strip()
    if not limpio:
        return False
    for caracter in limpio:
        if caracter.isalpha() or caracter in " -'":
            continue
        return False
    return True


def coincide_ciudad(lugar, ciudad):
    localidad = lugar.get("locality") or ""
    if not str(localidad).strip():
        return False
    return quitar_tildes(localidad) == quitar_tildes(ciudad)


def normalizar_ubicacion(lugar):
    coordenadas = lugar.get("coordinates") or {}
    resultado = {
        "id": str(lugar.get("id", "")),
        "ciudad": lugar.get("locality") or "",
        "nombre": lugar.get("name") or "",
        "fuente": "OpenAQ",
    }
    latitud = coordenadas.get("latitude")
    longitud = coordenadas.get("longitude")
    if latitud is not None and longitud is not None:
        resultado["latitud"] = latitud
        resultado["longitud"] = longitud
    return resultado


def crear_app(cliente=None):
    """Crea la aplicacion. La clave de OpenAQ solo se lee del entorno."""
    load_dotenv()
    app = Flask(__name__)
    app.cliente_openaq = cliente or ClienteOpenAQ()

    @app.get("/salud")
    def salud():
        clave = os.environ.get("OPENAQ_API_KEY", "").strip()
        return jsonify(
            {
                "estado": "ok",
                "servicio": "monitor-calidad-aire",
                "version": VERSION,
                "openaq_configurado": bool(clave),
            }
        )

    @app.get("/ubicaciones")
    def ubicaciones():
        ciudad = request.args.get("ciudad", "")
        if not ciudad_valida(ciudad):
            return respuesta_error(
                "ciudad_invalida",
                "Escribe el nombre de una ciudad, solo con letras.",
                400,
            )
        try:
            lugares = app.cliente_openaq.buscar_ubicaciones(iso="CO")
        except ErrorOpenAQ:
            return respuesta_error(
                "openaq_no_disponible",
                "OpenAQ no responde en este momento. Intenta de nuevo.",
                502,
            )

        encontradas = [
            normalizar_ubicacion(lugar)
            for lugar in lugares
            if coincide_ciudad(lugar, ciudad)
        ]
        return jsonify(encontradas)

    return app


app = crear_app()
