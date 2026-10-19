# Contrato de la API v1 · Monitor de Calidad del Aire

Versión del contrato: **1.0** · Esquema de almacenamiento: [`backend/db/schema_v1.sql`](../backend/db/schema_v1.sql)

Todas las respuestas son JSON (UTF-8), salvo la descarga del historial, que entrega un archivo CSV.
Las fechas usan formato ISO-8601 en UTC. La clave de OpenAQ nunca aparece en solicitudes ni respuestas.

## Resumen de endpoints

| Método | Ruta | Descripción | Historia |
|---|---|---|---|
| GET | `/salud` | Estado del servicio | - |
| GET | `/ubicaciones?ciudad=` | Estaciones disponibles de una ciudad | HU-MA-001 |
| POST | `/consultar` | Mediciones, AQI EPA y referencia OMS de una ciudad | HU-MA-001, HU-MA-002 |
| GET | `/historial` | Consultas guardadas, la más reciente primero | HU-MA-003 |
| GET | `/historial/descargar` | Historial en archivo CSV | HU-MA-003 |

La vista administrativa (HU-MA-004) queda fuera de la versión 1 del contrato.

---

## GET /salud

**Respuesta 200**

```json
{
  "estado": "ok",
  "servicio": "monitor-calidad-aire",
  "version": "0.1.0",
  "openaq_configurado": true
}
```

`openaq_configurado` indica solo si existe la variable de entorno; nunca devuelve la clave.

## GET /ubicaciones

**Parámetros de consulta:** `ciudad` (texto, obligatorio).

**Respuesta 200**

```json
[
  { "id": "E1", "ciudad": "Cali", "nombre": "Estación 1", "fuente": "OpenAQ" }
]
```

## POST /consultar

**Solicitud**

```json
{ "ciudad": "Cali" }
```

**Respuesta 200** (valores de ejemplo)

```json
{
  "ciudad": "Cali",
  "fecha_consulta": "2026-10-19T15:00:00Z",
  "fuente": "OpenAQ",
  "mediciones": [
    {
      "estacion_id": "E1",
      "contaminante": "pm25",
      "valor": 12.5,
      "unidad": "µg/m³",
      "periodo": "24h",
      "fecha_medicion": "2026-10-19T00:00:00Z"
    }
  ],
  "aqi_epa": { "indice": null, "categoria": null, "motivo": "pendiente de cálculo" },
  "referencia_oms": { "estado": "separada", "detalle": "No se mezcla con el AQI" }
}
```

Reglas:

- `contaminante` ∈ `pm25`, `no2`, `o3`; `periodo` ∈ `1h`, `8h`, `24h`.
- La unidad se devuelve **tal como la entrega OpenAQ**. El AQI EPA solo se calcula si unidad y periodo son compatibles; si no, `aqi_epa.indice` es `null` y `motivo` explica por qué.
- El AQI EPA y la referencia OMS van en campos **separados** y nunca se presentan como el mismo índice.
- El backend no inventa mediciones: si no hay datos, responde con error `sin_datos`.

## GET /historial

**Respuesta 200**, ordenada de la más reciente a la más antigua:

```json
[
  { "fecha_consulta": "2026-10-19T15:00:00Z", "ciudad": "Cali", "resultado": "ok", "fuente": "OpenAQ" }
]
```

Si no hay registros devuelve una lista vacía `[]` (estado vacío, no es un error).

## GET /historial/descargar

**Respuesta 200:** archivo `historial.csv` con las columnas `fecha_consulta, ciudad, resultado, fuente`.
Si todavía no hay registros responde **404** con `{"error": "historial_vacio"}`.

---

## Errores

Formato único: `{"error": "<codigo>", "mensaje": "<texto para el usuario>"}`

| HTTP | Código | Cuándo ocurre |
|---|---|---|
| 400 | `ciudad_invalida` | `ciudad` ausente, vacía o con formato inválido |
| 404 | `sin_datos` | La ciudad no tiene mediciones disponibles en OpenAQ |
| 404 | `historial_vacio` | Se pide descargar un historial sin registros |
| 502 | `openaq_no_disponible` | OpenAQ no responde, expira o devuelve error |
| 500 | `error_interno` | Falla inesperada del servidor (sin detalles internos al cliente) |

Una consulta con error **no** se escribe en el historial.

## Unidades

| Contaminante | Código | Unidad |
|---|---|---|
| Material particulado fino | `pm25` | Tal como la entrega OpenAQ (normalmente µg/m³) |
| Dióxido de nitrógeno | `no2` | Tal como la entrega OpenAQ (µg/m³ o ppm/ppb según la fuente) |
| Ozono | `o3` | Tal como la entrega OpenAQ (µg/m³ o ppm/ppb según la fuente) |

## Identificadores

| Entidad | Identificador |
|---|---|
| Estación | `estacion.id` (texto, el de OpenAQ) |
| Medición | `medicion.id` (entero autoincremental) |
| Consulta | `consulta.id` (entero autoincremental) |

## Regla de deduplicación

Una medición es **única** por la combinación `(estacion_id, contaminante, periodo, fecha_medicion)`.

- La restricción está definida en el esquema (`UNIQUE`) y se inserta con `INSERT OR IGNORE`.
- Repetir una consulta no crea mediciones duplicadas.
- Está verificada por la prueba `tests/test_esquema.py`.

## Versionado

- El contrato lleva versión (`1.0`) y el esquema de almacenamiento se versiona en `schema_v1.sql` con la tabla `esquema_version`.
- Un cambio incompatible genera `contrato_api_v2.md` y `schema_v2.sql`; los archivos anteriores se conservan.
