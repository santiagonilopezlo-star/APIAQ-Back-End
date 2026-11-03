from backend.app.normalizacion import normalizar_mediciones


def medicion(**cambios):
    base = {
        "estacion_id": "10",
        "contaminante": "pm25",
        "valor": 12.5,
        "unidad": "µg/m³",
        "periodo": "1h",
        "fecha_medicion": "2026-10-29T12:00:00Z",
        "fuente": "OpenAQ",
    }
    base.update(cambios)
    return base


def test_conserva_unidad_y_fecha():
    resultado = normalizar_mediciones(
        [
            medicion(),
            medicion(
                contaminante="no2",
                valor=0.02,
                unidad="ppm",
                fecha_medicion="2026-10-29T07:00:00-05:00",
            ),
        ],
    )

    assert resultado["avisos"] == []
    assert resultado["mediciones"][0]["unidad"] == "µg/m³"
    assert resultado["mediciones"][0]["valor"] == 12.5
    assert resultado["mediciones"][0]["fecha_medicion"] == "2026-10-29T12:00:00Z"
    assert resultado["mediciones"][0]["fuente"] == "OpenAQ"
    assert resultado["mediciones"][1]["unidad"] == "ppm"
    assert resultado["mediciones"][1]["valor"] == 0.02
    assert resultado["mediciones"][1]["fecha_medicion"] == "2026-10-29T12:00:00Z"


def test_rechaza_conversion_de_unidad():
    resultado = normalizar_mediciones(
        [medicion(unidad="ppm", valor=0.02, convertir_unidad=True)],
    )

    assert resultado["mediciones"] == []
    assert resultado["avisos"][0]["tipo"] == "conversion_rechazada"


def test_conserva_fechas_viejas_y_detecta_nulos_y_duplicados():
    reciente = medicion()
    resultado = normalizar_mediciones(
        [
            reciente,
            medicion(valor=None),
            dict(reciente),
            medicion(fecha_medicion="2024-09-05T16:00:00Z", valor=40),
            medicion(fuente="", valor=8),
        ],
    )

    tipos = [aviso["tipo"] for aviso in resultado["avisos"]]
    assert resultado["mediciones"] == [
        {
            "estacion_id": "10",
            "contaminante": "pm25",
            "valor": 12.5,
            "unidad": "µg/m³",
            "periodo": "1h",
            "fecha_medicion": "2026-10-29T12:00:00Z",
            "fuente": "OpenAQ",
        },
        {
            "estacion_id": "10",
            "contaminante": "pm25",
            "valor": 40.0,
            "unidad": "µg/m³",
            "periodo": "1h",
            "fecha_medicion": "2024-09-05T16:00:00Z",
            "fuente": "OpenAQ",
        },
    ]
    assert tipos == ["dato_nulo", "duplicado", "dato_nulo"]


def test_fecha_sin_zona_es_informacion_insuficiente():
    resultado = normalizar_mediciones(
        [medicion(fecha_medicion="2026-10-29 12:00:00")],
    )

    assert resultado["mediciones"] == []
    assert resultado["avisos"][0]["tipo"] == "fecha_invalida"
