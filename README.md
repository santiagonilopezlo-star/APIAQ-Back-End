# APIAQ Back-End · Monitor de Calidad del Aire

[![CI](https://github.com/santiagonilopezlo-star/APIAQ-Back-End/actions/workflows/ci.yml/badge.svg)](https://github.com/santiagonilopezlo-star/APIAQ-Back-End/actions/workflows/ci.yml)

Backend en Python del proyecto académico **Monitor de Calidad del Aire** (Universidad ECCI, Electiva I - Python).
Consulta mediciones de PM2.5, NO₂ y O₃ en la API v3 de OpenAQ, calcula el AQI de la EPA cuando los datos lo permiten, compara por separado con las guías de la OMS y registra el historial de consultas.

- **Equipo:** Johan Stwee Salgado Rodríguez · Santiago Nicolás López López
- **Interfaz web:** repositorio [-APIAQ-Front-End](https://github.com/santiagonilopezlo-star/-APIAQ-Front-End)
- **Contrato de la API:** [docs/contrato_api_v1.md](docs/contrato_api_v1.md)

> La información es orientativa y no reemplaza las alertas oficiales de las autoridades ambientales.

## Estructura del repositorio

```text
APIAQ-Back-End/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py              # API Flask y endpoint de salud (/salud)
│   └── db/
│       └── schema_v1.sql        # Esquema de almacenamiento versionado
├── tests/
│   ├── test_salud.py            # Prueba del endpoint de salud
│   └── test_esquema.py          # Prueba de la regla de deduplicación
├── docs/
│   └── contrato_api_v1.md       # Endpoints, errores, unidades y deduplicación
├── .github/
│   └── workflows/
│       └── ci.yml               # Integración continua: lint + pruebas
├── .env.example                 # Ejemplo de configuración (sin claves reales)
├── .gitignore
├── pytest.ini
├── requirements.txt             # Dependencias fijadas
└── README.md
```

## Módulos y responsabilidades

| Módulo | Responsabilidad |
|---|---|
| `backend/app` | API en Python: recibe peticiones de la interfaz web y coordina la consulta. |
| `backend/db` | Esquema de almacenamiento versionado (estaciones, mediciones, consultas). |
| `tests` | Pruebas automáticas mínimas. |
| `docs` | Contrato de la API y documentación técnica. |
| `.github/workflows` | Validaciones automáticas en cada cambio. |

## Arranque rápido

```bash
git clone https://github.com/santiagonilopezlo-star/APIAQ-Back-End.git
cd APIAQ-Back-End

python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # En Windows: copy .env.example .env
# Edita .env y escribe tu clave de OpenAQ

flask --app backend/app/main run
```

Comprobar que responde: abrir `http://127.0.0.1:5000/salud`.

## Configuración y seguridad

La clave de OpenAQ **solo vive en el servidor**, se lee desde la variable de entorno `OPENAQ_API_KEY` y nunca se escribe en el código ni se envía al navegador.

| Variable | Descripción |
|---|---|
| `OPENAQ_API_KEY` | Clave de la API v3 de OpenAQ. Se define en `.env`, que está en `.gitignore`. |

Nunca subas el archivo `.env`; usa `.env.example` como guía.

## Validaciones

```bash
ruff check .     # análisis estático (lint)
pytest -q        # pruebas del endpoint de salud y del esquema
```

Estos mismos comandos se ejecutan en GitHub Actions con cada `push` y `pull request`.

**Si el CI falla:** ejecuta los dos comandos anteriores en local, corrige el error que indiquen y vuelve a hacer `push`. El detalle del fallo está en la pestaña **Actions**.

## Flujo de trabajo y ramas

- `main`: rama estable; solo recibe cambios revisados.
- `desarrollo`: integración del trabajo en curso.
- `feature/<tarea>`: una rama por tarea (por ejemplo `feature/mca-14-contratos`).
- Todo cambio entra a `desarrollo` mediante *pull request* revisado por el otro integrante.

## Historias de usuario relacionadas

| Historia | Cubierta por |
|---|---|
| HU-MA-001 Consultar calidad del aire por ciudad | `POST /consultar` |
| HU-MA-002 Interpretar PM2.5, NO₂ y O₃ | Campos `aqi_epa` y `referencia_oms` de `POST /consultar` |
| HU-MA-003 Gráfica e historial | `GET /historial`, `GET /historial/descargar` |
| HU-MA-004 Vista administrativa | Pendiente para una iteración posterior |
