from flask import jsonify


def respuesta_error(codigo, mensaje, estado):
    """Formato único de error del contrato: error y mensaje."""
    return jsonify({"error": codigo, "mensaje": mensaje}), estado
