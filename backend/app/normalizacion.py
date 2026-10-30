from datetime import datetime, timedelta, timezone

CONTAMINANTES = {"pm25", "no2", "o3"}
PERIODOS = {"1h", "8h", "24h"}
DIAS_MAXIMOS = 7


def parsear_fecha(valor):
    """Convierte una fecha ISO-8601 a UTC. No inventa una fecha si falla."""
    if not isinstance(valor, str) or not valor.strip():
        return None
    texto = valor.strip()
    if texto.endswith("Z"):
        texto = texto[:-1] + "+00:00"
    try:
        fecha = datetime.fromisoformat(texto)
    except ValueError:
        return None
    if fecha.tzinfo is None:
        return None
    return fecha.astimezone(timezone.utc)


def _fecha_iso(fecha):
    return fecha.strftime("%Y-%m-%dT%H:%M:%SZ")


def normalizar_mediciones(crudas, ahora=None):
    """Deja solo mediciones utilizables. La unidad se conserva tal como llega."""
    if ahora is None:
        ahora = datetime.now(timezone.utc)
    elif ahora.tzinfo is None:
        ahora = ahora.replace(tzinfo=timezone.utc)

    buenas = []
    avisos = []
    vistas = set()

    for item in crudas:
        if not isinstance(item, dict):
            avisos.append({"tipo": "dato_nulo", "detalle": "medicion incompleta"})
            continue

        if item.get("convertir_unidad"):
            avisos.append(
                {
                    "tipo": "conversion_rechazada",
                    "detalle": "no se convierte la unidad",
                }
            )
            continue

        faltantes = []
        if item.get("valor") is None or item.get("valor") == "":
            faltantes.append("valor")
        if not item.get("contaminante"):
            faltantes.append("contaminante")
        if item.get("unidad") is None or str(item.get("unidad")).strip() == "":
            faltantes.append("unidad")
        if not item.get("fecha_medicion"):
            faltantes.append("fecha")
        if item.get("estacion_id") is None or str(item.get("estacion_id")).strip() == "":
            faltantes.append("estacion_id")
        if not item.get("fuente"):
            faltantes.append("fuente")
        if faltantes:
            avisos.append(
                {"tipo": "dato_nulo", "detalle": "faltan " + ", ".join(faltantes)}
            )
            continue

        contaminante = item["contaminante"]
        periodo = item.get("periodo")
        if contaminante not in CONTAMINANTES or periodo not in PERIODOS:
            avisos.append(
                {
                    "tipo": "informacion_insuficiente",
                    "detalle": "contaminante o periodo no soportado",
                }
            )
            continue

        try:
            valor = float(item["valor"])
        except (TypeError, ValueError):
            avisos.append({"tipo": "dato_nulo", "detalle": "valor no numerico"})
            continue

        fecha = parsear_fecha(item["fecha_medicion"])
        if fecha is None:
            avisos.append({"tipo": "fecha_invalida", "detalle": "fecha no reconocida"})
            continue

        if ahora - fecha > timedelta(days=DIAS_MAXIMOS):
            avisos.append(
                {"tipo": "dato_antiguo", "detalle": "la medicion tiene mas de 7 dias"}
            )
            continue

        fecha_iso = _fecha_iso(fecha)
        clave = (str(item["estacion_id"]), contaminante, periodo, fecha_iso)
        if clave in vistas:
            avisos.append({"tipo": "duplicado", "detalle": "medicion repetida"})
            continue
        vistas.add(clave)

        buenas.append(
            {
                "estacion_id": str(item["estacion_id"]),
                "contaminante": contaminante,
                "valor": valor,
                "unidad": str(item["unidad"]),
                "periodo": periodo,
                "fecha_medicion": fecha_iso,
                "fuente": str(item["fuente"]),
            }
        )

    return {"mediciones": buenas, "avisos": avisos}
