"""Genera graficas y estadisticas con pandas/matplotlib y las guarda como PNG."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from interfaz.analisis import mediciones_a_dataframe, resumen_consulta

CARPETA_IMAGENES = Path(__file__).resolve().parents[1] / "static" / "graficas"


def _asegurar_carpeta():
    CARPETA_IMAGENES.mkdir(parents=True, exist_ok=True)
    return CARPETA_IMAGENES


def _nombre_seguro(texto):
    limpio = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(texto or "x"))
    return limpio[:40] or "x"


def url_publica(nombre, base_url=None):
    """Arma URL absoluta para abrir la PNG en el navegador."""
    ruta = f"/static/graficas/{nombre}"
    if not base_url:
        return ruta
    return base_url.rstrip("/") + ruta


def generar_imagen_historial(filas, contaminante="pm25", estacion_id=None, base_url=None):
    """Guarda linea de historial. Devuelve dict con resumen y URL de navegador."""
    df = mediciones_a_dataframe(filas)
    resumen = resumen_consulta(df, contaminante)
    if df.empty:
        return {
            "estado": "vacio",
            "resumen": resumen,
            "archivo": None,
            "url": None,
            "detalle": "No hay mediciones para graficar",
        }

    carpeta = _asegurar_carpeta()
    nombre = f"historial_{_nombre_seguro(contaminante)}_{_nombre_seguro(estacion_id or 'todas')}.png"
    ruta = carpeta / nombre

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(
        df["fecha_medicion"],
        df["valor"],
        marker="o",
        linestyle="-",
        color="cornflowerblue",
        label=contaminante,
    )
    unidad = df["unidad"].iloc[0] if "unidad" in df.columns else ""
    ax.set_title(f"Historial {contaminante}")
    ax.set_xlabel("Fecha (UTC)")
    ax.set_ylabel(f"Valor ({unidad})" if unidad else "Valor")
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)

    return {
        "estado": "ok",
        "resumen": resumen,
        "archivo": nombre,
        "url": url_publica(nombre, base_url),
        "ruta": str(ruta),
    }


def generar_imagen_estadisticas(filas, base_url=None):
    """Barras de promedio/min/max por contaminante. Guarda PNG."""
    df = mediciones_a_dataframe(filas)
    if df.empty:
        return {
            "estado": "vacio",
            "resumen": resumen_consulta(df),
            "archivo": None,
            "url": None,
            "detalle": "No hay datos para estadisticas",
            "tabla": {},
        }

    tabla = (
        df.groupby("contaminante")
        .agg(Promedio=("valor", "mean"), Minimo=("valor", "min"), Maximo=("valor", "max"), Total=("valor", "count"))
        .round(3)
    )

    carpeta = _asegurar_carpeta()
    nombre = "estadisticas_contaminantes.png"
    ruta = carpeta / nombre

    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    tabla["Promedio"].plot(kind="bar", color="cornflowerblue", ax=axs[0])
    axs[0].set_title("Promedio por contaminante")
    axs[0].set_ylabel("Valor promedio")
    axs[0].grid(axis="y", linestyle="--", alpha=0.6)

    tabla["Total"].plot(kind="bar", color="seagreen", ax=axs[1])
    axs[1].set_title("Cantidad de mediciones")
    axs[1].set_ylabel("Total")
    axs[1].grid(axis="y", linestyle="--", alpha=0.6)

    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)

    return {
        "estado": "ok",
        "archivo": nombre,
        "url": url_publica(nombre, base_url),
        "ruta": str(ruta),
        "tabla": tabla.reset_index().to_dict(orient="records"),
        "resumen": resumen_consulta(df),
    }
