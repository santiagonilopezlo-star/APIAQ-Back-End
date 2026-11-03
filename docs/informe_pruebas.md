# Informe de pruebas manuales e integración con OpenAQ

Fecha de las pruebas automáticas: 2026-10-30.  
Fuente prevista: API v3 de OpenAQ (`https://api.openaq.org/v3`).  
No se usó base de datos.

## Qué se ejecutó

```bash
python -m pytest -q
```

25 pruebas, todas en verde. Usan respuestas JSON guardadas en `tests/datos/`. Ninguna prueba llama a OpenAQ ni escribe la clave.

Cubren:

- `GET /salud` con y sin `OPENAQ_API_KEY`, sin devolver la clave.
- Cliente: encabezado `X-API-Key`, timeout, páginas, tope de 5 páginas, HTTP 429 sin reintento, HTTP 503, JSON inválido y JSON sin `results`.
- `GET /ubicaciones`: ciudad con resultado, ciudad sin cobertura (`[]`) y ciudad vacía o con números (400).
- Normalización: unidad `µg/m³` y `ppm` sin convertir, fecha con offset a UTC, nulos y duplicados. Una fecha antigua no se descarta.
- `POST /consultar`: medición, ciudad inválida, sin datos, OpenAQ caído (502) y error interno (500) sin mostrar el detalle.

## Consulta real a Colombia

En el entorno de esta entrega no había `OPENAQ_API_KEY` (el archivo `.env` no existe y la variable no estaba definida). Por eso **no se lista ninguna ciudad**: no se consultó la API real y no se inventan localidades.

Para anotar las ciudades con estaciones, con la clave ya puesta en `.env`:

```bash
python -c "from backend.app.cliente_openaq import ClienteOpenAQ; lugares = ClienteOpenAQ().buscar_ubicaciones('CO'); print(sorted({(l.get('locality') or '').strip() for l in lugares}))"
```

Ese comando recorre `GET /v3/locations?iso=CO` con paginación. La clave se lee del entorno y no debe aparecer en la salida. La fecha de actualización de cada lectura está en `datetime.utc` de `GET /v3/locations/{id}/latest`.

Límites de OpenAQ usados por el cliente: 60 solicitudes por minuto y 2000 por hora. Si OpenAQ responde 429, el backend responde 502 y no vuelve a insistir.

## Ejemplos de respuesta

`GET /salud`

```json
{
  "estado": "ok",
  "servicio": "monitor-calidad-aire",
  "version": "0.1.0",
  "openaq_configurado": true
}
```

`GET /ubicaciones?ciudad=Bogota`

```json
[
  {
    "id": "10",
    "ciudad": "Bogotá",
    "nombre": "Estacion Centro",
    "fuente": "OpenAQ",
    "latitud": 4.65,
    "longitud": -74.08
  }
]
```

Si la ciudad es válida y no hay estaciones, la lista va vacía: `[]`.

`POST /consultar`

```json
{
  "ciudad": "Bogota",
  "fecha_consulta": "2026-10-30T15:00:00Z",
  "fuente": "OpenAQ",
  "mediciones": [
    {
      "estacion_id": "10",
      "contaminante": "pm25",
      "valor": 12.5,
      "unidad": "µg/m³",
      "periodo": "1h",
      "fecha_medicion": "2026-10-29T12:00:00Z"
    }
  ],
  "aqi_epa": {
    "indice": null,
    "categoria": null,
    "motivo": "Solo hay una lectura reciente de 1 h. No es un promedio de 24 h u 8 h y no se convierte la unidad."
  },
  "referencia_oms": {
    "estado": "separada",
    "detalle": "No se mezcla con el AQI"
  }
}
```

Error:

```json
{"error": "sin_datos", "mensaje": "No hay mediciones de PM2.5, NO2 u O3 para esa ciudad."}
```

## Diferencias frente al contrato v1

- No están `GET /historial` ni `GET /historial/descargar`. Esas rutas piden guardar consultas y esta entrega solo consulta OpenAQ.
- No está `backend/db/schema_v1.sql`. La deduplicación ocurre en memoria, solo dentro de la respuesta actual.
- `aqi_epa.indice` queda en `null`. La lectura de `/latest` no es un promedio de 24 h u 8 h y no se convierten unidades.
- `GET /ubicaciones` agrega `latitud` y `longitud` cuando OpenAQ las trae. Si no hay estaciones, responde `200` con `[]`. El `404 sin_datos` queda para `POST /consultar`.
- `periodo` de esta entrega es `1h` porque se usa la última lectura, no el recurso de promedios por horas.

## Cómo probar en Postman

1. Copia `.env.example` a `.env` y escribe la clave.
2. Arranca: `python -m flask --app backend/app/main run`
3. En Postman: Import → `postman/APIAQ.postman_collection.json`
4. La variable `baseUrl` ya apunta a `http://127.0.0.1:5000`.

`CiudadInventada` sirve para ver la búsqueda sin resultados y el error `sin_datos`. Esos dos casos sí necesitan que OpenAQ responda. Las pruebas automáticas cubren lo mismo con datos simulados.
