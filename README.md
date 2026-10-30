# APIAQ Back-End · Monitor de Calidad del Aire

[![CI](https://github.com/santiagonilopezlo-star/APIAQ-Back-End/actions/workflows/ci.yml/badge.svg)](https://github.com/santiagonilopezlo-star/APIAQ-Back-End/actions/workflows/ci.yml)

Backend en Python del proyecto académico **Monitor de Calidad del Aire** (Universidad ECCI, Electiva I - Python).
Consulta en vivo la API v3 de OpenAQ para estaciones de Colombia y devuelve PM2.5, NO₂ y O₃. No hay base de datos: cada petición va directo a OpenAQ.

- **Equipo:** Johan Stwee Salgado Rodríguez · Santiago Nicolás López López
- **Interfaz web:** repositorio [-APIAQ-Front-End](https://github.com/santiagonilopezlo-star/-APIAQ-Front-End)
- **Contrato de la API:** [contrato_api_v1.md](contrato_api_v1.md)
- **Colección de Postman:** [postman/APIAQ.postman_collection.json](postman/APIAQ.postman_collection.json)

> La información es orientativa y no reemplaza las alertas oficiales de las autoridades ambientales.

## Estructura del repositorio

```text
APIAQ-Back-End/
├── backend/
│   └── app/
│       ├── main.py              # Rutas Flask: /salud, /ubicaciones, /consultar
│       ├── cliente_openaq.py    # Llamadas a OpenAQ, paginación y tiempos de espera
│       ├── normalizacion.py     # Unidades, fechas, nulos, duplicados y datos viejos
│       └── errores.py           # Errores JSON del contrato
├── tests/                       # Pruebas con respuestas simuladas
├── docs/
│   ├── informe_pruebas.md
│   └── diccionario_datos.md
├── postman/
│   └── APIAQ.postman_collection.json
├── .github/workflows/ci.yml
├── .env.example
├── requirements.txt
└── README.md
```

`GET /historial` y la descarga CSV del contrato no están en esta entrega: harían falta guardar consultas.

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

Comprobar que responde: abrir `http://127.0.0.1:5000/salud`.

En Postman: Import y elige `postman/APIAQ.postman_collection.json`. La colección usa `http://127.0.0.1:5000`.

## Configuración y seguridad

La clave de OpenAQ solo vive en el servidor. Se lee de la variable `OPENAQ_API_KEY` y no se escribe en el código ni se envía al navegador.

| Variable | Descripción |
|---|---|
| `OPENAQ_API_KEY` | Clave de la API v3 de OpenAQ. Se define en `.env`, que está en `.gitignore`. |

## Endpoints de esta entrega

| Método | Ruta | Respuesta |
|---|---|---|
| GET | `/salud` | Estado del servicio y si la clave está configurada |
| GET | `/ubicaciones?ciudad=` | Estaciones de esa ciudad en Colombia |
| POST | `/consultar` | Mediciones recientes. Cuerpo: `{"ciudad": "Bogota"}` |

El AQI de la EPA queda en `null`: la lectura reciente no es un promedio de 24 h u 8 h y el backend no convierte unidades. La referencia de la OMS va en otro campo.

## Validaciones

```powershell
python -m pytest -q
```

GitHub Actions ejecuta esas pruebas en cada `push` y `pull request`.

## Ramas

- `main`: rama estable.
- `develop`: integración del trabajo en curso.
