"""Calculo del AQI de la EPA (US EPA).

Fuentes de breakpoints:
- PM2.5: promedio 24 h en µg/m³
- O3: promedio 8 h o 1 h en ppm
- NO2: promedio 1 h en ppb
"""

CATEGORIAS = [
    (50, "Buena"),
    (100, "Moderada"),
    (150, "Dañina para grupos sensibles"),
    (200, "Dañina"),
    (300, "Muy dañina"),
    (500, "Peligrosa"),
]

# (contaminante, periodo, unidad_normalizada, truncar_decimales, breakpoints)
# breakpoints: lista de (c_low, c_high, i_low, i_high)
TABLAS = {
    ("pm25", "24h", "ug/m3"): (
        1,
        [
            (0.0, 12.0, 0, 50),
            (12.1, 35.4, 51, 100),
            (35.5, 55.4, 101, 150),
            (55.5, 150.4, 151, 200),
            (150.5, 250.4, 201, 300),
            (250.5, 350.4, 301, 400),
            (350.5, 500.4, 401, 500),
        ],
    ),
    ("o3", "8h", "ppm"): (
        3,
        [
            (0.000, 0.054, 0, 50),
            (0.055, 0.070, 51, 100),
            (0.071, 0.085, 101, 150),
            (0.086, 0.105, 151, 200),
            (0.106, 0.200, 201, 300),
        ],
    ),
    ("o3", "1h", "ppm"): (
        3,
        [
            (0.125, 0.164, 101, 150),
            (0.165, 0.204, 151, 200),
            (0.205, 0.404, 201, 300),
            (0.405, 0.504, 301, 400),
            (0.505, 0.604, 401, 500),
        ],
    ),
    ("no2", "1h", "ppb"): (
        0,
        [
            (0, 53, 0, 50),
            (54, 100, 51, 100),
            (101, 360, 101, 150),
            (361, 649, 151, 200),
            (650, 1249, 201, 300),
            (1250, 1649, 301, 400),
            (1650, 2049, 401, 500),
        ],
    ),
}

ESTANDAR = "US EPA AQI"


def normalizar_unidad(unidad):
    texto = str(unidad or "").strip().lower().replace("µ", "u").replace("μ", "u")
    texto = texto.replace(" ", "")
    if texto in {"ug/m3", "ug/m³", "ugm3"}:
        return "ug/m3"
    if texto == "ppm":
        return "ppm"
    if texto == "ppb":
        return "ppb"
    return texto


def categoria_aqi(indice):
    for tope, nombre in CATEGORIAS:
        if indice <= tope:
            return nombre
    return "Peligrosa"


def truncar(valor, decimales):
    if decimales <= 0:
        return int(valor)
    factor = 10 ** decimales
    return int(valor * factor) / factor


def aqi_desde_concentracion(valor, contaminante, periodo, unidad):
    """Devuelve indice AQI o None si no aplica."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    if numero < 0:
        return None

    clave = (contaminante, periodo, normalizar_unidad(unidad))
    tabla = TABLAS.get(clave)
    if tabla is None:
        return None

    decimales, tramos = tabla
    concentracion = truncar(numero, decimales)
    for c_low, c_high, i_low, i_high in tramos:
        if c_low <= concentracion <= c_high:
            bruto = (i_high - i_low) / (c_high - c_low) * (concentracion - c_low) + i_low
            return int(round(bruto))
    return None


def calcular_aqi(mediciones):
    """Elige el AQI mas alto entre mediciones compatibles con EPA."""
    if not mediciones:
        return {
            "indice": None,
            "categoria": None,
            "estandar": ESTANDAR,
            "motivo": "No hay mediciones para calcular el AQI",
            "contaminante": None,
        }

    mejor = None
    for item in mediciones:
        indice = aqi_desde_concentracion(
            item.get("valor"),
            item.get("contaminante"),
            item.get("periodo"),
            item.get("unidad"),
        )
        if indice is None:
            continue
        candidato = {
            "indice": indice,
            "categoria": categoria_aqi(indice),
            "estandar": ESTANDAR,
            "motivo": None,
            "contaminante": item.get("contaminante"),
            "periodo": item.get("periodo"),
            "unidad": item.get("unidad"),
            "estacion_id": item.get("estacion_id"),
        }
        if mejor is None or candidato["indice"] > mejor["indice"]:
            mejor = candidato

    if mejor is not None:
        return mejor

    return {
        "indice": None,
        "categoria": None,
        "estandar": ESTANDAR,
        "motivo": (
            "Unidad o periodo no compatibles con EPA. "
            "PM2.5 necesita 24h en µg/m³; O3 necesita 1h/8h en ppm; "
            "NO2 necesita 1h en ppb. No se convierten unidades."
        ),
        "contaminante": None,
    }
