import os
import unicodedata
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from backend.app.cliente_openaq import ClienteOpenAQ, ErrorOpenAQ
from backend.app.errores import respuesta_error
from backend.app.normalizacion import normalizar_mediciones

VERSION = "0.1.0"
MAX_ESTACIONES = 5
CONTAMINANTES = {"pm25", "no2", "o3"}
MOTIVO_AQI = (
    "Solo hay una lectura reciente de 1 h. "
    "No es un promedio de 24 h u 8 h y no se convierte la unidad."
)


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


def crudas_desde_lectura(lugar, lecturas):
    sensores = {}
    for sensor in lugar.get("sensors") or []:
        sensores[sensor.get("id")] = sensor

    crudas = []
    for lectura in lecturas or []:
        sensor = sensores.get(lectura.get("sensorsId"))
        parametro = (sensor or {}).get("parameter") or {}
        nombre = parametro.get("name")
        if nombre not in CONTAMINANTES:
            continue
        momento = lectura.get("datetime")
        fecha = momento.get("utc") if isinstance(momento, dict) else None
        crudas.append(
            {
                "estacion_id": lugar.get("id"),
                "contaminante": nombre,
                "valor": lectura.get("value"),
                "unidad": parametro.get("units"),
                "periodo": "1h",
                "fecha_medicion": fecha,
                "fuente": "OpenAQ",
            }
        )
    return crudas


def armar_consulta(ciudad, mediciones):
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    publicas = []
    for item in mediciones:
        publicas.append(
            {
                "estacion_id": item["estacion_id"],
                "contaminante": item["contaminante"],
                "valor": item["valor"],
                "unidad": item["unidad"],
                "periodo": item["periodo"],
                "fecha_medicion": item["fecha_medicion"],
            }
        )
    return {
        "ciudad": ciudad.strip(),
        "fecha_consulta": ahora,
        "fuente": "OpenAQ",
        "mediciones": publicas,
        "aqi_epa": {"indice": None, "categoria": None, "motivo": MOTIVO_AQI},
        "referencia_oms": {
            "estado": "separada",
            "detalle": "No se mezcla con el AQI",
        },
    }


def consultar_ciudad(cliente, ciudad):
    lugares = [
        lugar
        for lugar in cliente.buscar_ubicaciones(iso="CO")
        if coincide_ciudad(lugar, ciudad)
    ]
    crudas = []
    for lugar in lugares[:MAX_ESTACIONES]:
        lecturas = cliente.ultima_lectura(lugar.get("id"))
        crudas.extend(crudas_desde_lectura(lugar, lecturas))

    utiles = normalizar_mediciones(crudas)["mediciones"]
    if not utiles:
        return None
    return armar_consulta(ciudad, utiles)


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

    @app.post("/consultar")
    def consultar():
        cuerpo = request.get_json(silent=True)
        ciudad = cuerpo.get("ciudad", "") if isinstance(cuerpo, dict) else ""
        if not ciudad_valida(ciudad):
            return respuesta_error(
                "ciudad_invalida",
                "Escribe el nombre de una ciudad, solo con letras.",
                400,
            )
        try:
            resultado = consultar_ciudad(app.cliente_openaq, ciudad)
        except ErrorOpenAQ:
            return respuesta_error(
                "openaq_no_disponible",
                "OpenAQ no responde en este momento. Intenta de nuevo.",
                502,
            )
        except Exception:
            return respuesta_error(
                "error_interno",
                "Ocurrió un error inesperado.",
                500,
            )
        if resultado is None:
            return respuesta_error(
                "sin_datos",
                "No hay mediciones recientes de PM2.5, NO2 u O3 para esa ciudad.",
                404,
            )
        return jsonify(resultado)

    return app


app = crear_app()
