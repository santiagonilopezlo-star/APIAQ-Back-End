from backend.app.aqi import aqi_desde_concentracion, calcular_aqi, categoria_aqi


def test_umbrales_pm25_referencia_epa():
    # Valores de referencia EPA (concentracion truncada a 1 decimal)
    assert aqi_desde_concentracion(0.0, "pm25", "24h", "µg/m³") == 0
    assert aqi_desde_concentracion(12.0, "pm25", "24h", "ug/m3") == 50
    assert aqi_desde_concentracion(12.1, "pm25", "24h", "µg/m³") == 51
    assert aqi_desde_concentracion(35.4, "pm25", "24h", "µg/m³") == 100
    assert aqi_desde_concentracion(35.5, "pm25", "24h", "µg/m³") == 101
    assert aqi_desde_concentracion(55.4, "pm25", "24h", "µg/m³") == 150
    assert aqi_desde_concentracion(55.5, "pm25", "24h", "µg/m³") == 151
    assert aqi_desde_concentracion(150.4, "pm25", "24h", "µg/m³") == 200
    assert aqi_desde_concentracion(250.4, "pm25", "24h", "µg/m³") == 300
    assert aqi_desde_concentracion(350.4, "pm25", "24h", "µg/m³") == 400
    assert aqi_desde_concentracion(500.4, "pm25", "24h", "µg/m³") == 500


def test_redondeo_y_truncamiento_pm25():
    # 12.049 se trunca a 12.0 -> AQI 50
    assert aqi_desde_concentracion(12.049, "pm25", "24h", "µg/m³") == 50
    # Valor intermedio del tramo moderado
    assert aqi_desde_concentracion(20.0, "pm25", "24h", "µg/m³") == 68


def test_valores_invalidos_y_datos_insuficientes():
    assert aqi_desde_concentracion(-1, "pm25", "24h", "µg/m³") is None
    assert aqi_desde_concentracion("x", "pm25", "24h", "µg/m³") is None
    assert aqi_desde_concentracion(12.0, "pm25", "1h", "µg/m³") is None
    assert aqi_desde_concentracion(12.0, "pm25", "24h", "ppm") is None
    assert aqi_desde_concentracion(0.08, "o3", "8h", "µg/m³") is None


def test_o3_y_no2_compatibles():
    assert aqi_desde_concentracion(0.054, "o3", "8h", "ppm") == 50
    assert aqi_desde_concentracion(0.125, "o3", "1h", "ppm") == 101
    assert aqi_desde_concentracion(53, "no2", "1h", "ppb") == 50
    assert aqi_desde_concentracion(100, "no2", "1h", "ppb") == 100


def test_calcular_aqi_elige_el_mayor_y_devuelve_estandar():
    resultado = calcular_aqi(
        [
            {
                "estacion_id": "1",
                "contaminante": "pm25",
                "valor": 12.0,
                "unidad": "µg/m³",
                "periodo": "24h",
            },
            {
                "estacion_id": "1",
                "contaminante": "pm25",
                "valor": 55.5,
                "unidad": "µg/m³",
                "periodo": "24h",
            },
        ]
    )
    assert resultado["indice"] == 151
    assert resultado["categoria"] == categoria_aqi(151)
    assert resultado["estandar"] == "US EPA AQI"
    assert resultado["motivo"] is None


def test_calcular_aqi_sin_compatibles():
    resultado = calcular_aqi(
        [
            {
                "estacion_id": "1",
                "contaminante": "pm25",
                "valor": 12.0,
                "unidad": "µg/m³",
                "periodo": "1h",
            }
        ]
    )
    assert resultado["indice"] is None
    assert resultado["categoria"] is None
    assert "compatibles" in resultado["motivo"]
