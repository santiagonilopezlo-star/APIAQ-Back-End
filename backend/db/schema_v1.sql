-- Esquema v1 del monitor de calidad del aire (SQLite).

CREATE TABLE IF NOT EXISTS esquema_version (
    version TEXT PRIMARY KEY,
    aplicado_en TEXT NOT NULL
);

INSERT OR IGNORE INTO esquema_version (version, aplicado_en)
VALUES ('1.0', datetime('now'));

CREATE TABLE IF NOT EXISTS estaciones (
    id TEXT PRIMARY KEY,
    ciudad TEXT NOT NULL,
    nombre TEXT NOT NULL,
    fuente TEXT NOT NULL DEFAULT 'OpenAQ'
);

CREATE TABLE IF NOT EXISTS consultas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_consulta TEXT NOT NULL,
    ciudad TEXT NOT NULL,
    resultado TEXT NOT NULL,
    fuente TEXT NOT NULL DEFAULT 'OpenAQ'
);

CREATE TABLE IF NOT EXISTS mediciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estacion_id TEXT NOT NULL,
    contaminante TEXT NOT NULL,
    valor REAL NOT NULL,
    unidad TEXT NOT NULL,
    periodo TEXT NOT NULL,
    fecha_medicion TEXT NOT NULL,
    fuente TEXT NOT NULL DEFAULT 'OpenAQ',
    UNIQUE (estacion_id, contaminante, periodo, fecha_medicion),
    FOREIGN KEY (estacion_id) REFERENCES estaciones(id)
);

CREATE INDEX IF NOT EXISTS idx_mediciones_filtros
ON mediciones (estacion_id, contaminante, fecha_medicion);
