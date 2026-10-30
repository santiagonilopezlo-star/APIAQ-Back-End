import os

from dotenv import load_dotenv
from flask import Flask, jsonify

VERSION = "0.1.0"


def crear_app():
    """Crea la aplicacion. La clave de OpenAQ solo se lee del entorno."""
    load_dotenv()
    app = Flask(__name__)

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

    return app


app = crear_app()
