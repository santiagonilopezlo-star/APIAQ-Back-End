# Diccionario de datos

Esta entrega no guarda datos. Cada respuesta sale de OpenAQ en el momento de la consulta. La clave de la API no es un dato de respuesta.

## Ubicación (`GET /ubicaciones`)

| Campo | Tipo | Origen | Notas |
|---|---|---|---|
| `id` | texto | `location.id` de OpenAQ | Se devuelve como texto |
| `ciudad` | texto | `location.locality` | Nombre tal como lo trae OpenAQ |
| `nombre` | texto | `location.name` | Nombre de la estación |
| `fuente` | texto | fijo | Siempre `OpenAQ` |
| `latitud` | número | `coordinates.latitude` | Solo si OpenAQ envía las dos coordenadas |
| `longitud` | número | `coordinates.longitude` | Solo si OpenAQ envía las dos coordenadas |

La búsqueda compara `locality` con la ciudad pedida sin distinguir mayúsculas ni tildes. `Bogota` coincide con `Bogotá`. No coincide si el texto de OpenAQ trae palabras extra, por ejemplo `Bogotá D.C.`.

## Medición (dentro de `POST /consultar`)

| Campo | Tipo | Origen | Notas |
|---|---|---|---|
| `estacion_id` | texto | `location.id` | Estación de la lectura |
| `contaminante` | texto | `sensor.parameter.name` | Solo `pm25`, `no2` y `o3` |
| `valor` | número | `latest.value` | No se convierte |
| `unidad` | texto | `sensor.parameter.units` | Se conserva tal como llega (`µg/m³`, `ppm`, etc.) |
| `periodo` | texto | fijo en esta entrega | `1h`: es la última lectura, no un promedio calculado por nosotros |
| `fecha_medicion` | texto | `latest.datetime.utc` | ISO-8601 en UTC, con `Z` |

Parámetros de OpenAQ usados al interpretar el sensor: `pm25` (id 2), `no2` (id 7), `o3` (id 10). El filtro de país es `iso=CO`.

## Consulta (`POST /consultar`)

| Campo | Tipo | Notas |
|---|---|---|
| `ciudad` | texto | La ciudad pedida, sin espacios al borde |
| `fecha_consulta` | texto | Momento en que respondió este servidor, UTC |
| `fuente` | texto | `OpenAQ` |
| `mediciones` | lista | Solo lecturas que pasaron la normalización |
| `aqi_epa.indice` | nulo | En esta entrega no se calcula |
| `aqi_epa.categoria` | nulo | En esta entrega no se calcula |
| `aqi_epa.motivo` | texto | Explica que la lectura es de 1 h y que no se convierte la unidad |
| `referencia_oms.estado` | texto | `separada` |
| `referencia_oms.detalle` | texto | Recuerda que no es el mismo índice que el AQI |

## Avisos internos de normalización

No salen en la API. Sirven para las pruebas y para decidir si la consulta queda en `sin_datos`.

| Tipo | Cuándo |
|---|---|
| `dato_nulo` | Falta valor, contaminante, unidad, fecha, estación o fuente, o el valor no es numérico |
| `duplicado` | Ya se vio la misma estación, contaminante, periodo y fecha |
| `dato_antiguo` | La fecha tiene más de 7 días |
| `fecha_invalida` | La fecha no es ISO-8601 con zona horaria |
| `conversion_rechazada` | La medición pide convertir la unidad |
| `informacion_insuficiente` | Contaminante o periodo fuera de `pm25`/`no2`/`o3` y `1h`/`8h`/`24h` |

## Errores

| HTTP | `error` | Cuándo |
|---|---|---|
| 400 | `ciudad_invalida` | Ciudad ausente, vacía o con números o símbolos |
| 404 | `sin_datos` | No hay estación en Colombia para esa ciudad, o ninguna medición reciente usable |
| 502 | `openaq_no_disponible` | Timeout, sin conexión, HTTP 429 o error 5xx de OpenAQ |
| 500 | `error_interno` | Falla inesperada. El mensaje no incluye el detalle interno |
