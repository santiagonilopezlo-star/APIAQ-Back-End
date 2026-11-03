from backend.app.oms import comparar_medicion, comparar_oms


def test_pm25_dentro_y_sobre_guia_24h():
    dentro = comparar_medicion(
        {
            "contaminante": "pm25",
            "valor": 10.0,
            "unidad": "µg/m³",
            "periodo": "24h",
        }
    )
    sobre = comparar_medicion(
        {
            "contaminante": "pm25",
            "valor": 20.0,
            "unidad": "µg/m³",
            "periodo": "24h",
        }
    )

    assert dentro["estado"] == "dentro_guia"
    assert dentro["version"] == "OMS AQG 2021"
    assert dentro["periodo_guia"] == "24h"
    assert dentro["valor_guia"] == 15.0
    assert dentro["diferencia"] == -5.0
    assert dentro["separada_del_aqi"] is True

    assert sobre["estado"] == "sobre_guia"
    assert sobre["diferencia"] == 5.0


def test_periodo_incompatible_es_dato_insuficiente():
    resultado = comparar_medicion(
        {
            "contaminante": "pm25",
            "valor": 12.0,
            "unidad": "µg/m³",
            "periodo": "1h",
        }
    )
    assert resultado["estado"] == "dato_insuficiente"
    assert resultado["periodo_guia"] == "24h"
    assert "24h" in resultado["detalle"]


def test_unidad_incompatible_no_convierte():
    resultado = comparar_medicion(
        {
            "contaminante": "o3",
            "valor": 0.08,
            "unidad": "ppm",
            "periodo": "8h",
        }
    )
    assert resultado["estado"] == "dato_insuficiente"
    assert "No se convierte" in resultado["detalle"]


def test_comparar_oms_separa_del_aqi():
    resultado = comparar_oms(
        [
            {
                "contaminante": "pm25",
                "valor": 15.0,
                "unidad": "µg/m³",
                "periodo": "24h",
            }
        ]
    )
    assert resultado["estado"] == "dentro_guia"
    assert "no es el mismo indice" in resultado["detalle_aqi"]
    assert len(resultado["comparaciones"]) == 1
