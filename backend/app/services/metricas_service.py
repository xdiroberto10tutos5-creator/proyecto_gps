from datetime import datetime, timezone

from fastapi import HTTPException

from app.services.calculos import haversine
from app.supabase_client import (
    delete_metricas_by_sesion_jugador,
    get_gps_by_sesion,
    get_gps_by_sesion_jugador,
    get_metricas_by_sesion,
    get_metricas_by_sesion_jugador,
    insert_metricas
)

PERFIL_CALCULO = "juvenil_amateur_14_18"
UMBRAL_HSR = 4.5      # 16.2 km/h
UMBRAL_SPRINT = 5.8   # 20.9 km/h
UMBRAL_DECELERACION = -1.5  # m/s²
VELOCIDAD_MIN_DECELERACION = UMBRAL_HSR
PRECISION_MAXIMA = 30
MOVIMIENTO_MINIMO = 0.5
DISTANCIA_MINIMA_SESION = 8
VELOCIDAD_MAXIMA_REALISTA = 10.5  # 37.8 km/h


def obtener_perfil_calculo():
    return {
        "perfil": PERFIL_CALCULO,
        "rango_edad": "14-18 años",
        "nivel": "amateur",
        "hsr_desde_kmh": round(UMBRAL_HSR * 3.6, 1),
        "sprint_desde_kmh": round(UMBRAL_SPRINT * 3.6, 1),
        "deceleracion_desde_ms2": UMBRAL_DECELERACION,
        "deceleracion_velocidad_min_kmh": round(VELOCIDAD_MIN_DECELERACION * 3.6, 1),
        "precision_maxima_m": PRECISION_MAXIMA,
        "movimiento_minimo_m": MOVIMIENTO_MINIMO,
        "distancia_minima_sesion_m": DISTANCIA_MINIMA_SESION,
        "velocidad_maxima_admitida_kmh": round(VELOCIDAD_MAXIMA_REALISTA * 3.6, 1),
    }


def parse_timestamp(value):
    if not value:
        return None

    try:
        timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None

    if timestamp.tzinfo:
        timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)

    return timestamp


def obtener_puntos_gps(sesion_id, jugador_id=None):
    if jugador_id:
        return get_gps_by_sesion_jugador(sesion_id, jugador_id)

    return get_gps_by_sesion(sesion_id)


def calcular_metricas_desde_puntos(gps):
    distancia = 0
    hsr = 0
    sprints = 0
    deceleraciones = 0
    velocidades = []
    duracion_seg = 0
    segmentos_validos = 0
    segmentos_descartados = 0
    velocidad_anterior_valida = None
    en_sprint = False
    en_deceleracion = False

    for i in range(1, len(gps)):
        p1 = gps[i - 1]
        p2 = gps[i]
        precision = float(p2.get("precision_gps") or 0)

        if precision and precision > PRECISION_MAXIMA:
            segmentos_descartados += 1
            continue

        d = haversine(
            float(p1["latitud"]),
            float(p1["longitud"]),
            float(p2["latitud"]),
            float(p2["longitud"])
        )

        t1 = parse_timestamp(p1.get("timestamp"))
        t2 = parse_timestamp(p2.get("timestamp"))
        dt = (t2 - t1).total_seconds() if t1 and t2 else 3

        if dt <= 0:
            segmentos_descartados += 1
            continue

        if dt > 10:
            dt = 3

        if d < MOVIMIENTO_MINIMO:
            continue

        velocidad_gps = float(p2.get("velocidad") or 0)
        velocidad_distancia = d / dt
        velocidad = velocidad_gps if velocidad_gps > 0 else velocidad_distancia

        if velocidad > VELOCIDAD_MAXIMA_REALISTA:
            segmentos_descartados += 1
            continue

        if velocidad < 0.5:
            velocidad = 0

        aceleracion = (
            (velocidad - velocidad_anterior_valida) / dt
            if velocidad_anterior_valida is not None
            else 0
        )

        distancia += d
        duracion_seg += dt
        segmentos_validos += 1
        velocidades.append(velocidad)

        deceleracion_intensa = (
            aceleracion <= UMBRAL_DECELERACION
            and velocidad_anterior_valida is not None
            and velocidad_anterior_valida >= VELOCIDAD_MIN_DECELERACION
        )

        if deceleracion_intensa:
            if not en_deceleracion:
                deceleraciones += 1
            en_deceleracion = True
        else:
            en_deceleracion = False

        if velocidad >= UMBRAL_HSR:
            hsr += d

        if velocidad >= UMBRAL_SPRINT:
            if not en_sprint:
                sprints += 1
            en_sprint = True
        else:
            en_sprint = False

        velocidad_anterior_valida = velocidad

    vmax = max(velocidades) if velocidades else 0
    duracion_min = duracion_seg / 60
    dist_min = distancia / duracion_min if duracion_min > 0 else 0

    if distancia < DISTANCIA_MINIMA_SESION:
        distancia = 0
        vmax = 0
        hsr = 0
        sprints = 0
        deceleraciones = 0
        dist_min = 0

    return {
        "distancia_metros": round(distancia, 2),
        "velocidad_max_ms": round(vmax, 2),
        "velocidad_max_kmh": round(vmax * 3.6, 2),
        "hsr_metros": round(hsr, 2),
        "sprints": sprints,
        "deceleraciones": deceleraciones,
        "distancia_por_minuto": round(dist_min, 2),
        "puntos_gps": len(gps),
        "segmentos_validos": segmentos_validos,
        "segmentos_descartados": segmentos_descartados,
        "perfil_calculo": obtener_perfil_calculo()
    }


def calcular_metricas_sesion(sesion_id, jugador_id=None):
    gps = obtener_puntos_gps(sesion_id, jugador_id)
    return calcular_metricas_desde_puntos(gps)


def construir_metricas_guardar(sesion_id, jugador_id, resultado):
    return {
        "sesion_id": sesion_id,
        "jugador_id": jugador_id,
        "distancia_total": resultado["distancia_metros"],
        "velocidad_max": resultado["velocidad_max_kmh"],
        "hsr": resultado["hsr_metros"],
        "sprints": resultado["sprints"],
        "deceleraciones": resultado["deceleraciones"],
        "dist_min": resultado["distancia_por_minuto"]
    }


def guardar_metricas_calculadas(sesion_id, jugador_id):
    if not jugador_id:
        raise HTTPException(
            status_code=400,
            detail="jugador_id es requerido para guardar métricas"
        )

    resultado = calcular_metricas_sesion(sesion_id, jugador_id)
    data = construir_metricas_guardar(sesion_id, jugador_id, resultado)

    # Evita duplicados cuando el mismo lote se reenvía para una sesión/jugador.
    delete_metricas_by_sesion_jugador(sesion_id, jugador_id)
    guardado = insert_metricas(data)

    return {
        "calculadas": resultado,
        "guardadas": guardado
    }


def obtener_metricas_guardadas(sesion_id, jugador_id=None):
    if jugador_id:
        return get_metricas_by_sesion_jugador(sesion_id, jugador_id)

    return get_metricas_by_sesion(sesion_id)
