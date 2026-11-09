"""Analisis basico del historial con pandas y matplotlib.

Sigue el estilo del ejercicio Reportes.py: DataFrame, resumen y grafica.
No inventa mediciones en huecos: solo dibuja los puntos que existen.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

UNIDADES = {
    "pm25": "µg/m³",
    "no2": "µg/m³ o ppb/ppm",
    "o3": "µg/m³ o ppm",
}


def mediciones_a_dataframe(filas):
    """Convierte la lista JSON del API en un DataFrame ordenado por fecha."""
    if not filas:
        return pd.DataFrame(
            columns=[
                "estacion_id",
                "contaminante",
                "valor",
                "unidad",
                "periodo",
                "fecha_medicion",
                "fuente",
            ]
        )

    df = pd.DataFrame(filas)
    df["valor"] = pd.to_numeric(df.get("valor"), errors="coerce")
    df["fecha_medicion"] = pd.to_datetime(df.get("fecha_medicion"), utc=True, errors="coerce")
    df = df.dropna(subset=["valor", "fecha_medicion"])
    df = df.sort_values("fecha_medicion")
    return df.reset_index(drop=True)


def resumen_consulta(df, contaminante=None):
    """Resumen simple para mostrar en la interfaz."""
    if df is None or df.empty:
        return {
            "estado": "vacio",
            "total": 0,
            "promedio": None,
            "minimo": None,
            "maximo": None,
            "contaminante": contaminante,
            "unidad": UNIDADES.get(contaminante, ""),
            "detalle": "No hay mediciones en el rango seleccionado",
        }

    serie = df["valor"]
    return {
        "estado": "ok",
        "total": int(len(df)),
        "promedio": round(float(serie.mean()), 3),
        "minimo": round(float(serie.min()), 3),
        "maximo": round(float(serie.max()), 3),
        "contaminante": contaminante or (df["contaminante"].iloc[0] if "contaminante" in df else None),
        "unidad": df["unidad"].iloc[0] if "unidad" in df else "",
        "detalle": f"{len(df)} mediciones sin rellenar huecos",
    }


def generar_grafica_historial(df, contaminante, ruta_salida=None, titulo=None):
    """Grafica de linea con puntos. Huecos quedan visibles (sin interpolar)."""
    if df is None or df.empty:
        return None

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(
        df["fecha_medicion"],
        df["valor"],
        marker="o",
        linestyle="-",
        color="cornflowerblue",
        label=contaminante or "medicion",
    )
    unidad = df["unidad"].iloc[0] if "unidad" in df.columns and len(df) else ""
    ax.set_title(titulo or f"Historial de {contaminante}")
    ax.set_xlabel("Fecha (UTC)")
    ax.set_ylabel(f"Valor ({unidad})" if unidad else "Valor")
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()

    if ruta_salida:
        destino = Path(ruta_salida)
        destino.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(destino)

    return fig


def exportar_reporte_excel(df, ruta_salida):
    """Guarda un resumen tipo ejercicio institucional."""
    if df is None or df.empty:
        raise ValueError("No hay datos para exportar")

    resumen = df.groupby("contaminante").agg(
        Promedio=("valor", "mean"),
        Minimo=("valor", "min"),
        Maximo=("valor", "max"),
        Total=("valor", "count"),
    )
    resumen.to_excel(ruta_salida)
    return resumen
