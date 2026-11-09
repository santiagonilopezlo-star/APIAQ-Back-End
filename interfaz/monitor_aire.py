"""
Monitor de Calidad del Aire - interfaz basica (Tkinter).

Guia de estilo: ejercicio Reportes.py (pandas + matplotlib + Tkinter).
Habla con el backend local Flask. No muestra claves ni detalles internos.
"""

import os
import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import requests

from interfaz.analisis import (
    exportar_reporte_excel,
    generar_grafica_historial,
    mediciones_a_dataframe,
    resumen_consulta,
)

URL_BASE = os.environ.get("APIAQ_URL", "http://127.0.0.1:5000")
CONTAMINANTES = ("pm25", "no2", "o3")


class MonitorAire:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Calidad del Aire")
        self.root.geometry("1000x720")
        self.root.minsize(760, 560)
        self.root.configure(bg="#f2f2f2")

        self.estaciones = []
        self.ultima_consulta = None
        self.canvas_grafico = None

        self._armar_ui()
        self._vincular_teclado()
        self.mostrar_estado("Esperando accion del usuario...")

    def _armar_ui(self):
        titulo = tk.Label(
            self.root,
            text="Monitor de Calidad del Aire",
            font=("Arial", 16, "bold"),
            bg="#f2f2f2",
        )
        titulo.pack(pady=8)

        # --- Busqueda de ciudad / estaciones ---
        marco_busqueda = tk.LabelFrame(
            self.root, text="Buscar y seleccionar estacion", bg="#f2f2f2", padx=8, pady=8
        )
        marco_busqueda.pack(fill="x", padx=12, pady=6)

        tk.Label(marco_busqueda, text="Ciudad:", bg="#f2f2f2").grid(row=0, column=0, sticky="w")
        self.entrada_ciudad = tk.Entry(marco_busqueda, width=28)
        self.entrada_ciudad.grid(row=0, column=1, padx=5, pady=4, sticky="ew")
        self.entrada_ciudad.insert(0, "Medellin")

        self.btn_buscar = tk.Button(
            marco_busqueda,
            text="Buscar estaciones",
            command=self.buscar_estaciones,
            bg="#74b9ff",
            width=18,
        )
        self.btn_buscar.grid(row=0, column=2, padx=5)

        tk.Label(marco_busqueda, text="Estacion:", bg="#f2f2f2").grid(row=1, column=0, sticky="w")
        self.combo_estaciones = ttk.Combobox(marco_busqueda, state="readonly", width=60)
        self.combo_estaciones.grid(row=1, column=1, columnspan=2, padx=5, pady=4, sticky="ew")

        self.btn_consultar = tk.Button(
            marco_busqueda,
            text="Consultar mediciones",
            command=self.consultar_mediciones,
            bg="#55efc4",
            width=18,
        )
        self.btn_consultar.grid(row=0, column=3, rowspan=2, padx=8)

        marco_busqueda.columnconfigure(1, weight=1)

        # --- Resultados AQI / OMS ---
        self.marco_resultados = tk.LabelFrame(
            self.root, text="Mediciones, AQI EPA y referencia OMS", bg="#f2f2f2", padx=8, pady=8
        )
        self.marco_resultados.pack(fill="both", expand=False, padx=12, pady=6)

        self.txt_resultados = tk.Text(
            self.marco_resultados, height=10, wrap="word", font=("Consolas", 10)
        )
        self.txt_resultados.pack(fill="both", expand=True)
        self.txt_resultados.insert("1.0", "Aun no hay resultados.\n")
        self.txt_resultados.config(state="disabled")

        # --- Historial / filtros / grafica ---
        marco_hist = tk.LabelFrame(
            self.root, text="Historial (pandas + matplotlib)", bg="#f2f2f2", padx=8, pady=8
        )
        marco_hist.pack(fill="both", expand=True, padx=12, pady=6)

        fila_filtros = tk.Frame(marco_hist, bg="#f2f2f2")
        fila_filtros.pack(fill="x")

        tk.Label(fila_filtros, text="Contaminante:", bg="#f2f2f2").pack(side="left")
        self.combo_contaminante = ttk.Combobox(
            fila_filtros, values=CONTAMINANTES, state="readonly", width=8
        )
        self.combo_contaminante.set("pm25")
        self.combo_contaminante.pack(side="left", padx=4)

        tk.Label(fila_filtros, text="Desde (UTC):", bg="#f2f2f2").pack(side="left", padx=(10, 0))
        self.entrada_desde = tk.Entry(fila_filtros, width=22)
        self.entrada_desde.insert(0, "2020-01-01T00:00:00Z")
        self.entrada_desde.pack(side="left", padx=4)

        tk.Label(fila_filtros, text="Hasta (UTC):", bg="#f2f2f2").pack(side="left")
        self.entrada_hasta = tk.Entry(fila_filtros, width=22)
        self.entrada_hasta.insert(0, "2030-01-01T00:00:00Z")
        self.entrada_hasta.pack(side="left", padx=4)

        self.btn_grafica = tk.Button(
            fila_filtros, text="Graficar historial", command=self.graficar_historial, bg="#fab1a0"
        )
        self.btn_grafica.pack(side="left", padx=6)

        self.btn_excel = tk.Button(
            fila_filtros, text="Exportar Excel", command=self.exportar_excel, bg="#ffeaa7"
        )
        self.btn_excel.pack(side="left", padx=4)

        self.btn_reintentar = tk.Button(
            fila_filtros, text="Reintentar", command=self.reintentar, bg="#81ecec"
        )
        self.btn_reintentar.pack(side="right", padx=4)

        self.lbl_resumen = tk.Label(
            marco_hist, text="Resumen: sin consulta", bg="#f2f2f2", anchor="w", justify="left"
        )
        self.lbl_resumen.pack(fill="x", pady=4)

        self.frame_grafico = tk.Frame(marco_hist, bg="white", bd=2, relief="groove")
        self.frame_grafico.pack(fill="both", expand=True, pady=4)

        self.lbl_estado = tk.Label(
            self.root, text="", bg="#f2f2f2", fg="gray", font=("Arial", 10), anchor="w"
        )
        self.lbl_estado.pack(fill="x", padx=12, pady=6)

    def _vincular_teclado(self):
        # Enter busca; flechas mueven el combo de estaciones (Tkinter/ttk nativo).
        self.entrada_ciudad.bind("<Return>", lambda _e: self.buscar_estaciones())
        self.root.bind("<Control-r>", lambda _e: self.reintentar())
        self.btn_buscar.focus_set()

    def mostrar_estado(self, texto, error=False):
        self.lbl_estado.config(text=texto, fg="#c0392b" if error else "gray")

    def escribir_resultados(self, texto):
        self.txt_resultados.config(state="normal")
        self.txt_resultados.delete("1.0", tk.END)
        self.txt_resultados.insert("1.0", texto)
        self.txt_resultados.config(state="disabled")

    def mensaje_api(self, respuesta):
        """Traduce errores del API a texto usable. Nunca muestra claves."""
        try:
            datos = respuesta.json()
        except ValueError:
            return "El servidor respondio de forma inesperada. Intenta de nuevo."
        codigo = datos.get("error", "")
        mensaje = datos.get("mensaje", "Ocurrio un problema.")
        if codigo == "ciudad_invalida":
            return "Ciudad invalida. Escribe solo letras."
        if codigo == "sin_datos":
            return "Sin resultados: no hay mediciones para esa ciudad."
        if codigo == "openaq_no_disponible":
            return "OpenAQ no responde ahora. Usa Reintentar."
        if codigo == "historial_vacio":
            return "Historial vacio. Primero consulta una ciudad."
        return mensaje

    def pedir(self, metodo, ruta, cuerpo=None, timeout=40):
        url = URL_BASE + ruta
        if metodo == "GET":
            return requests.get(url, timeout=timeout)
        return requests.post(url, json=cuerpo, timeout=timeout)

    def buscar_estaciones(self):
        ciudad = self.entrada_ciudad.get().strip()
        self.mostrar_estado("Cargando estaciones...")
        self.combo_estaciones.set("")
        self.combo_estaciones["values"] = []
        self.estaciones = []
        try:
            respuesta = self.pedir("GET", f"/ubicaciones?ciudad={ciudad}")
        except requests.RequestException:
            self.mostrar_estado("No se pudo conectar con el backend.", error=True)
            messagebox.showerror(
                "Error de conexion",
                "No hay conexion con el servidor local.\n"
                "Arranca: python -m flask --app backend/app/main run",
            )
            return

        if respuesta.status_code != 200:
            texto = self.mensaje_api(respuesta)
            self.mostrar_estado(texto, error=True)
            messagebox.showwarning("Busqueda", texto)
            return

        self.estaciones = respuesta.json()
        if not self.estaciones:
            self.mostrar_estado("Sin resultados para esa ciudad.", error=True)
            self.escribir_resultados("Sin estaciones.\nPrueba otra ciudad (ej. Medellin, Bogota).")
            messagebox.showinfo("Sin resultados", "No hay estaciones para esa ciudad.")
            return

        etiquetas = [
            f"{e.get('id')} | {e.get('nombre')} | {e.get('ciudad')}" for e in self.estaciones
        ]
        self.combo_estaciones["values"] = etiquetas
        self.combo_estaciones.current(0)
        self.mostrar_estado(f"{len(self.estaciones)} estaciones encontradas.")

    def estacion_seleccionada(self):
        idx = self.combo_estaciones.current()
        if idx < 0 or idx >= len(self.estaciones):
            return None
        return self.estaciones[idx]

    def consultar_mediciones(self):
        ciudad = self.entrada_ciudad.get().strip()
        self.mostrar_estado("Cargando mediciones, AQI y OMS...")
        try:
            respuesta = self.pedir("POST", "/consultar", {"ciudad": ciudad})
        except requests.RequestException:
            self.mostrar_estado("Error de conexion al consultar.", error=True)
            messagebox.showerror("Error", "No se pudo consultar. Revisa que el backend este activo.")
            return

        if respuesta.status_code != 200:
            texto = self.mensaje_api(respuesta)
            self.mostrar_estado(texto, error=True)
            self.escribir_resultados(texto)
            messagebox.showwarning("Consulta", texto)
            return

        datos = respuesta.json()
        self.ultima_consulta = datos
        self.escribir_resultados(self.formatear_resultados(datos))
        self.mostrar_estado("Consulta lista. AQI y OMS van en campos separados.")

    def formatear_resultados(self, datos):
        lineas = []
        lineas.append(f"Ciudad: {datos.get('ciudad')}")
        lineas.append(f"Fecha consulta: {datos.get('fecha_consulta')}")
        lineas.append(f"Fuente: {datos.get('fuente')}")
        lineas.append("")
        lineas.append("=== Mediciones ===")
        for m in datos.get("mediciones") or []:
            lineas.append(
                f"- Estacion {m.get('estacion_id')} | {m.get('contaminante')} = "
                f"{m.get('valor')} {m.get('unidad')} | periodo {m.get('periodo')} | "
                f"fecha {m.get('fecha_medicion')}"
            )
        if not datos.get("mediciones"):
            lineas.append("(sin mediciones)")

        aqi = datos.get("aqi_epa") or {}
        lineas.append("")
        lineas.append("=== AQI EPA (indice) ===")
        if aqi.get("indice") is None:
            lineas.append(f"Indice: no calculado")
            lineas.append(f"Motivo: {aqi.get('motivo')}")
            lineas.append("Leyenda: sin categoria porque faltan unidad/periodo compatibles.")
        else:
            lineas.append(f"Indice: {aqi.get('indice')}")
            lineas.append(f"Categoria: {aqi.get('categoria')}")
            lineas.append(f"Estandar: {aqi.get('estandar')}")
            lineas.append("Leyenda: Buena / Moderada / Danina... segun EPA.")

        oms = datos.get("referencia_oms") or {}
        lineas.append("")
        lineas.append("=== Referencia OMS (NO es el AQI) ===")
        lineas.append(f"Estado: {oms.get('estado')}")
        lineas.append(f"Guia/version: {oms.get('version') or oms.get('guia')}")
        lineas.append(f"Periodo guia: {oms.get('periodo_guia')}")
        lineas.append(f"Valor guia: {oms.get('valor_guia')} {oms.get('unidad_guia')}")
        lineas.append(f"Detalle: {oms.get('detalle')}")
        if oms.get("detalle_aqi"):
            lineas.append(oms.get("detalle_aqi"))
        return "\n".join(lineas)

    def graficar_historial(self):
        contaminante = self.combo_contaminante.get().strip() or "pm25"
        desde = self.entrada_desde.get().strip()
        hasta = self.entrada_hasta.get().strip()
        estacion = self.estacion_seleccionada()
        params = f"contaminante={contaminante}&desde={desde}&hasta={hasta}"
        if estacion:
            params += f"&estacion_id={estacion.get('id')}"

        self.mostrar_estado("Cargando historial...")
        try:
            respuesta = self.pedir("GET", f"/historial/mediciones?{params}")
        except requests.RequestException:
            self.mostrar_estado("Error al leer historial.", error=True)
            messagebox.showerror("Error", "No se pudo leer el historial.")
            return

        if respuesta.status_code != 200:
            texto = self.mensaje_api(respuesta)
            self.mostrar_estado(texto, error=True)
            messagebox.showwarning("Historial", texto)
            return

        filas = respuesta.json()
        df = mediciones_a_dataframe(filas)
        resumen = resumen_consulta(df, contaminante)
        self.lbl_resumen.config(
            text=(
                f"Resumen: estado={resumen['estado']} | total={resumen['total']} | "
                f"promedio={resumen['promedio']} | min={resumen['minimo']} | "
                f"max={resumen['maximo']} | {resumen['detalle']}"
            )
        )

        for widget in self.frame_grafico.winfo_children():
            widget.destroy()

        if resumen["estado"] == "vacio":
            vacio = tk.Label(
                self.frame_grafico,
                text="Estado vacio: no hay puntos para graficar.\n"
                "Consulta una ciudad primero o cambia el rango.",
                bg="white",
                fg="#7f8c8d",
                font=("Arial", 11),
            )
            vacio.pack(expand=True)
            self.mostrar_estado("Historial vacio para esos filtros.", error=True)
            return

        fig = generar_grafica_historial(
            df,
            contaminante,
            ruta_salida=os.path.join("interfaz", "salida", f"historial_{contaminante}.png"),
            titulo=f"Historial {contaminante} (sin inventar huecos)",
        )
        self.canvas_grafico = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        self.canvas_grafico.draw()
        self.canvas_grafico.get_tk_widget().pack(fill="both", expand=True)
        self.mostrar_estado("Grafica lista. Ejes etiquetados; huecos no rellenados.")

    def exportar_excel(self):
        contaminante = self.combo_contaminante.get().strip() or "pm25"
        desde = self.entrada_desde.get().strip()
        hasta = self.entrada_hasta.get().strip()
        try:
            respuesta = self.pedir(
                "GET",
                f"/historial/mediciones?contaminante={contaminante}&desde={desde}&hasta={hasta}",
            )
            filas = respuesta.json() if respuesta.status_code == 200 else []
            df = mediciones_a_dataframe(filas)
            ruta = os.path.join("interfaz", "salida", "reporte_historial.xlsx")
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            exportar_reporte_excel(df, ruta)
            messagebox.showinfo("Excel", f"Reporte guardado en {ruta}")
            self.mostrar_estado("Reporte Excel generado.")
        except Exception:
            messagebox.showwarning("Excel", "No hay datos suficientes para exportar.")
            self.mostrar_estado("No se pudo exportar Excel.", error=True)

    def reintentar(self):
        self.mostrar_estado("Reintentando ultima busqueda...")
        if self.entrada_ciudad.get().strip():
            self.buscar_estaciones()


def main():
    root = tk.Tk()
    MonitorAire(root)
    root.mainloop()


if __name__ == "__main__":
    main()
