import sqlite3
from pathlib import Path

from backend.app.almacen import Almacen, RUTA_SCHEMA


def test_esquema_tiene_unique_de_mediciones(tmp_path):
    db = tmp_path / "schema.db"
    Almacen(ruta_db=db)

    conexion = sqlite3.connect(db)
    fila = conexion.execute(
        """
        SELECT sql FROM sqlite_master
        WHERE type = 'table' AND name = 'mediciones'
        """
    ).fetchone()
    conexion.close()

    assert "UNIQUE (estacion_id, contaminante, periodo, fecha_medicion)" in fila[0]
    assert "1.0" in RUTA_SCHEMA.read_text(encoding="utf-8")
