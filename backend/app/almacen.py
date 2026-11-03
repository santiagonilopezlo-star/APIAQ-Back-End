import csv
import io
import sqlite3
from pathlib import Path

RUTA_DB_DEFAULT = Path(__file__).resolve().parents[1] / "db" / "monitor.db"
RUTA_SCHEMA = Path(__file__).resolve().parents[1] / "db" / "schema_v1.sql"


class Almacen:
    """Persistencia sencilla en SQLite. Sin ORM, nivel electiva."""

    def __init__(self, ruta_db=None):
        self.ruta_db = Path(ruta_db) if ruta_db else RUTA_DB_DEFAULT
        self.ruta_db.parent.mkdir(parents=True, exist_ok=True)
        self._iniciar()

    def _conectar(self):
        conexion = sqlite3.connect(self.ruta_db)
        conexion.row_factory = sqlite3.Row
        return conexion

    def _iniciar(self):
        script = RUTA_SCHEMA.read_text(encoding="utf-8")
        with self._conectar() as conexion:
            conexion.executescript(script)

    def guardar_consulta_ok(self, ciudad, fecha_consulta, fuente, mediciones):
        with self._conectar() as conexion:
            conexion.execute(
                """
                INSERT INTO consultas (fecha_consulta, ciudad, resultado, fuente)
                VALUES (?, ?, 'ok', ?)
                """,
                (fecha_consulta, ciudad, fuente),
            )
            for item in mediciones:
                conexion.execute(
                    """
                    INSERT OR IGNORE INTO estaciones (id, ciudad, nombre, fuente)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        str(item["estacion_id"]),
                        ciudad,
                        str(item["estacion_id"]),
                        item.get("fuente", fuente),
                    ),
                )
                conexion.execute(
                    """
                    INSERT OR IGNORE INTO mediciones (
                        estacion_id, contaminante, valor, unidad,
                        periodo, fecha_medicion, fuente
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(item["estacion_id"]),
                        item["contaminante"],
                        float(item["valor"]),
                        item["unidad"],
                        item["periodo"],
                        item["fecha_medicion"],
                        item.get("fuente", fuente),
                    ),
                )

    def listar_consultas(self):
        with self._conectar() as conexion:
            filas = conexion.execute(
                """
                SELECT fecha_consulta, ciudad, resultado, fuente
                FROM consultas
                ORDER BY fecha_consulta DESC, id DESC
                """
            ).fetchall()
        return [dict(fila) for fila in filas]

    def csv_consultas(self):
        filas = self.listar_consultas()
        if not filas:
            return None
        salida = io.StringIO()
        escritor = csv.DictWriter(
            salida,
            fieldnames=["fecha_consulta", "ciudad", "resultado", "fuente"],
        )
        escritor.writeheader()
        escritor.writerows(filas)
        return salida.getvalue()

    def listar_mediciones(self, estacion_id=None, contaminante=None, desde=None, hasta=None):
        sql = [
            """
            SELECT estacion_id, contaminante, valor, unidad, periodo,
                   fecha_medicion, fuente
            FROM mediciones
            WHERE 1 = 1
            """
        ]
        params = []
        if estacion_id:
            sql.append("AND estacion_id = ?")
            params.append(str(estacion_id))
        if contaminante:
            sql.append("AND contaminante = ?")
            params.append(contaminante)
        if desde:
            sql.append("AND fecha_medicion >= ?")
            params.append(desde)
        if hasta:
            sql.append("AND fecha_medicion <= ?")
            params.append(hasta)
        sql.append("ORDER BY fecha_medicion ASC, id ASC")

        with self._conectar() as conexion:
            filas = conexion.execute("\n".join(sql), params).fetchall()
        return [dict(fila) for fila in filas]
