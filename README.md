# APIAQ Back-End · Monitor de Calidad del Aire

[![CI](https://github.com/santiagonilopezlo-star/APIAQ-Back-End/actions/workflows/ci.yml/badge.svg)](https://github.com/santiagonilopezlo-star/APIAQ-Back-End/actions/workflows/ci.yml)

Backend en Python del proyecto académico **Monitor de Calidad del Aire** (Universidad ECCI, Electiva I - Python).
Consulta OpenAQ v3, calcula AQI EPA cuando unidad y periodo son compatibles, compara por separado con la guía OMS AQG 2021 y guarda historial en SQLite.

- **Equipo:** Johan Stwee Salgado Rodríguez · Santiago Nicolás López López
- **Interfaz web:** repositorio [-APIAQ-Front-End](https://github.com/santiagonilopezlo-star/-APIAQ-Front-End)
- **Contrato de la API:** [contrato_api_v1.md](contrato_api_v1.md)
- **Colección de Postman:** [postman/APIAQ.postman_collection.json](postman/APIAQ.postman_collection.json)

> La información es orientativa y no reemplaza las alertas oficiales de las autoridades ambientales.

## Estructura del repositorio

```text
APIAQ-Back-End/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── cliente_openaq.py
│   │   ├── normalizacion.py
│   │   ├── aqi.py
│   │   ├── oms.py
│   │   ├── almacen.py
│   │   └── errores.py
│   └── db/
│       ├── schema_v1.sql
│       └── monitor.db          # se crea al correr; no se sube a Git
├── tests/
├── docs/
├── postman/
├── .env.example
├── requirements.txt
└── README.md
```

## Arranque en Windows

```powershell
git clone https://github.com/santiagonilopezlo-star/APIAQ-Back-End.git
cd APIAQ-Back-End

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
# Edita .env y escribe tu clave de OpenAQ

python -m flask --app backend/app/main run
```

Comprobar: `http://127.0.0.1:5000/salud`.  
Postman: Import → `postman/APIAQ.postman_collection.json`.

## Endpoints

| Método | Ruta | Respuesta |
|---|---|---|
| GET | `/salud` | Estado del servicio |
| GET | `/ubicaciones?ciudad=` | Estaciones en Colombia |
| POST | `/consultar` | Mediciones + `aqi_epa` + `referencia_oms`; guarda historial si sale bien |
| GET | `/historial` | Consultas guardadas, más reciente primero |
| GET | `/historial/descargar` | CSV del historial |
| GET | `/historial/mediciones` | Mediciones con filtros `estacion_id`, `contaminante`, `desde`, `hasta` |

AQI EPA solo si unidad y periodo coinciden (PM2.5 24h µg/m³, O3 1h/8h ppm, NO2 1h ppb). Sin conversión de unidades. OMS va en campo aparte.

## Validaciones

```powershell
python -m pytest -q
```

## Ramas

- `main`: estable
- `develop`: trabajo en curso
