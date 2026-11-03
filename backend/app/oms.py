"""Comparacion con las guias de calidad del aire de la OMS (AQG 2021).

La referencia sanitaria va separada del AQI EPA. No se mezcla ni se convierte
en un indice AQI.
"""

from backend.app.aqi import normalizar_unidad

VERSION_GUIA = "OMS AQG 2021"

# Contaminante -> periodo_guia -> (valor_guia, unidad)
GUIAS = {
    "pm25": {
        "24h": (15.0, "ug/m3"),
        "anual": (5.0, "ug/m3"),
    },
    "no2": {
        "24h": (25.0, "ug/m3"),
        "anual": (10.0, "ug/m3"),
    },
    "o3": {
        "8h": (100.0, "ug/m3"),
    },
}

# Que periodo de medicion puede compararse con cada guia
COMPATIBLES = {
    ("pm25", "24h"): "24h",
    ("no2", "24h"): "24h",
    ("o3", "8h"): "8h",
}


def comparar_medicion(medicion):
    contaminante = medicion.get("contaminante")
    periodo = medicion.get("periodo")
    unidad = normalizar_unidad(medicion.get("unidad"))
    guias = GUIAS.get(contaminante)

    if guias is None:
        return {
            "estado": "guia_no_aplicable",
            "guia": VERSION_GUIA,
            "version": VERSION_GUIA,
            "periodo_guia": None,
            "valor_guia": None,
            "unidad_guia": None,
            "valor_medido": medicion.get("valor"),
            "unidad_medida": medicion.get("unidad"),
            "diferencia": None,
            "contaminante": contaminante,
            "detalle": "No hay guia OMS para ese contaminante en esta entrega",
            "separada_del_aqi": True,
        }

    periodo_guia = COMPATIBLES.get((contaminante, periodo))
    if periodo_guia is None:
        ejemplo = next(iter(guias.items()))
        return {
            "estado": "dato_insuficiente",
            "guia": VERSION_GUIA,
            "version": VERSION_GUIA,
            "periodo_guia": ejemplo[0],
            "valor_guia": ejemplo[1][0],
            "unidad_guia": "µg/m³",
            "valor_medido": medicion.get("valor"),
            "unidad_medida": medicion.get("unidad"),
            "diferencia": None,
            "contaminante": contaminante,
            "detalle": (
                f"La guia OMS para {contaminante} usa promedio {ejemplo[0]}. "
                f"La medicion tiene periodo {periodo}."
            ),
            "separada_del_aqi": True,
        }

    valor_guia, unidad_guia = guias[periodo_guia]
    if unidad != unidad_guia:
        return {
            "estado": "dato_insuficiente",
            "guia": VERSION_GUIA,
            "version": VERSION_GUIA,
            "periodo_guia": periodo_guia,
            "valor_guia": valor_guia,
            "unidad_guia": "µg/m³",
            "valor_medido": medicion.get("valor"),
            "unidad_medida": medicion.get("unidad"),
            "diferencia": None,
            "contaminante": contaminante,
            "detalle": (
                "La unidad de la medicion no coincide con la guia OMS. "
                "No se convierte la unidad."
            ),
            "separada_del_aqi": True,
        }

    try:
        valor = float(medicion.get("valor"))
    except (TypeError, ValueError):
        return {
            "estado": "dato_insuficiente",
            "guia": VERSION_GUIA,
            "version": VERSION_GUIA,
            "periodo_guia": periodo_guia,
            "valor_guia": valor_guia,
            "unidad_guia": "µg/m³",
            "valor_medido": medicion.get("valor"),
            "unidad_medida": medicion.get("unidad"),
            "diferencia": None,
            "contaminante": contaminante,
            "detalle": "El valor medido no es numerico",
            "separada_del_aqi": True,
        }

    diferencia = round(valor - valor_guia, 3)
    if valor <= valor_guia:
        estado = "dentro_guia"
        detalle = "El valor no supera la guia sanitaria OMS"
    else:
        estado = "sobre_guia"
        detalle = "El valor supera la guia sanitaria OMS"

    return {
        "estado": estado,
        "guia": VERSION_GUIA,
        "version": VERSION_GUIA,
        "periodo_guia": periodo_guia,
        "valor_guia": valor_guia,
        "unidad_guia": "µg/m³",
        "valor_medido": valor,
        "unidad_medida": medicion.get("unidad"),
        "diferencia": diferencia,
        "contaminante": contaminante,
        "detalle": detalle,
        "separada_del_aqi": True,
    }


def comparar_oms(mediciones):
    if not mediciones:
        return {
            "estado": "dato_insuficiente",
            "guia": VERSION_GUIA,
            "version": VERSION_GUIA,
            "periodo_guia": None,
            "valor_guia": None,
            "detalle": "No hay mediciones para comparar con la OMS",
            "separada_del_aqi": True,
            "comparaciones": [],
        }

    comparaciones = [comparar_medicion(item) for item in mediciones]
    # Prioriza una comparacion completa si existe
    principal = next(
        (c for c in comparaciones if c["estado"] in {"dentro_guia", "sobre_guia"}),
        comparaciones[0],
    )
    resultado = dict(principal)
    resultado["comparaciones"] = comparaciones
    resultado["detalle_aqi"] = (
        "La referencia OMS es sanitaria y no es el mismo indice que el AQI EPA"
    )
    return resultado
