from pathlib import Path

from interfaz.analisis import (
    exportar_reporte_excel,
    generar_grafica_historial,
    mediciones_a_dataframe,
    resumen_consulta,
)


def filas_ejemplo():
    return [
        {
            "estacion_id": "10",
            "contaminante": "pm25",
            "valor": 12.5,
            "unidad": "µg/m³",
            "periodo": "1h",
            "fecha_medicion": "2024-09-01T10:00:00Z",
            "fuente": "OpenAQ",
        },
        {
            "estacion_id": "10",
            "contaminante": "pm25",
            "valor": 20.0,
            "unidad": "µg/m³",
            "periodo": "1h",
            "fecha_medicion": "2024-09-05T16:00:00Z",
            "fuente": "OpenAQ",
        },
    ]


def test_dataframe_ordena_por_fecha_y_omite_nulos():
    filas = filas_ejemplo() + [
        {
            "estacion_id": "10",
            "contaminante": "pm25",
            "valor": None,
            "unidad": "µg/m³",
            "periodo": "1h",
            "fecha_medicion": "2024-09-03T00:00:00Z",
            "fuente": "OpenAQ",
        }
    ]
    df = mediciones_a_dataframe(filas)
    assert len(df) == 2
    assert df.iloc[0]["valor"] == 12.5
    assert str(df.iloc[0]["fecha_medicion"]) < str(df.iloc[1]["fecha_medicion"])


def test_resumen_vacio_y_con_datos():
    vacio = resumen_consulta(mediciones_a_dataframe([]), "pm25")
    ok = resumen_consulta(mediciones_a_dataframe(filas_ejemplo()), "pm25")
    assert vacio["estado"] == "vacio"
    assert vacio["total"] == 0
    assert ok["estado"] == "ok"
    assert ok["total"] == 2
    assert ok["promedio"] == 16.25


def test_grafica_no_inventa_puntos(tmp_path):
    df = mediciones_a_dataframe(filas_ejemplo())
    ruta = tmp_path / "hist.png"
    fig = generar_grafica_historial(df, "pm25", ruta_salida=ruta)
    assert fig is not None
    assert ruta.exists()
    # Solo hay 2 puntos de datos en la linea
    linea = fig.axes[0].lines[0]
    assert len(linea.get_xdata()) == 2
    assert len(linea.get_ydata()) == 2


def test_exportar_excel(tmp_path):
    df = mediciones_a_dataframe(filas_ejemplo())
    ruta = tmp_path / "reporte.xlsx"
    resumen = exportar_reporte_excel(df, ruta)
    assert ruta.exists()
    assert "pm25" in resumen.index
