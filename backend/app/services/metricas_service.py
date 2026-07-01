from datetime import datetime, timezone
from math import cos, pi

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
ACELERACION_MAXIMA_REALISTA = 5.0
TOLERANCIA_SUAVIZADO_CAMINATA = 5.0
MARGEN_VELOCIDAD_GPS = 1.8


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
        "aceleracion_maxima_admitida_ms2": ACELERACION_MAXIMA_REALISTA,
        "tolerancia_suavizado_caminata_m": TOLERANCIA_SUAVIZADO_CAMINATA,
        "margen_velocidad_gps_ms": MARGEN_VELOCIDAD_GPS,
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


def distancia_punto_segmento(p, a, b):
    dx = b["x"] - a["x"]
    dy = b["y"] - a["y"]
    if dx == 0 and dy == 0:
        return ((p["x"] - a["x"]) ** 2 + (p["y"] - a["y"]) ** 2) ** 0.5

    t = ((p["x"] - a["x"]) * dx + (p["y"] - a["y"]) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))
    proy_x = a["x"] + t * dx
    proy_y = a["y"] + t * dy
    return ((p["x"] - proy_x) ** 2 + (p["y"] - proy_y) ** 2) ** 0.5


def simplificar_indices(locales, inicio, fin, tolerancia):
    mayor_distancia = 0
    mayor_indice = None

    for i in range(inicio + 1, fin):
        distancia = distancia_punto_segmento(locales[i], locales[inicio], locales[fin])
        if distancia > mayor_distancia:
            mayor_distancia = distancia
            mayor_indice = i

    if mayor_indice is not None and mayor_distancia > tolerancia:
        izquierda = simplificar_indices(locales, inicio, mayor_indice, tolerancia)
        derecha = simplificar_indices(locales, mayor_indice, fin, tolerancia)
        return izquierda[:-1] + derecha

    return [inicio, fin]


def suavizar_puntos_caminata(gps):
    if len(gps) < 4:
        return gps

    velocidades_distancia = []
    for i in range(1, len(gps)):
        t1 = parse_timestamp(gps[i - 1].get("timestamp"))
        t2 = parse_timestamp(gps[i].get("timestamp"))
        dt = (t2 - t1).total_seconds() if t1 and t2 else 0
        if dt <= 0:
            continue
        d = haversine(
            float(gps[i - 1]["latitud"]),
            float(gps[i - 1]["longitud"]),
            float(gps[i]["latitud"]),
            float(gps[i]["longitud"])
        )
        velocidades_distancia.append(d / dt)

    if max(velocidades_distancia or [0]) >= UMBRAL_HSR:
        return gps

    precisiones = sorted(float(p.get("precision_gps") or 0) for p in gps if p.get("precision_gps"))
    precision_media = precisiones[len(precisiones) // 2] if precisiones else 10
    tolerancia = max(TOLERANCIA_SUAVIZADO_CAMINATA, min(12, precision_media * 0.75))

    ref_lat = float(gps[0]["latitud"])
    ref_lon = float(gps[0]["longitud"])
    metros_lat = 111320
    metros_lon = 111320 * cos(ref_lat * pi / 180)
    locales = []
    for p in gps:
        lat = float(p["latitud"])
        lon = float(p["longitud"])
        locales.append({
            "x": (lat - ref_lat) * metros_lat,
            "y": (lon - ref_lon) * metros_lon,
        })

    indices = simplificar_indices(locales, 0, len(locales) - 1, tolerancia)
    if len(indices) < 2:
        return gps

    return [gps[i] for i in indices]


def velocidad_confiable(velocidad_gps, velocidad_distancia):
    if velocidad_gps <= 0:
        return velocidad_distancia

    if velocidad_distancia <= 0:
        return 0

    diferencia = abs(velocidad_gps - velocidad_distancia)
    if diferencia > MARGEN_VELOCIDAD_GPS and velocidad_gps > velocidad_distancia:
        return velocidad_distancia

    return min(velocidad_gps, velocidad_distancia + MARGEN_VELOCIDAD_GPS)


def calcular_metricas_desde_puntos(gps):
    puntos_originales = len(gps)
    gps = suavizar_puntos_caminata(gps)
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
    hsr_distancia_actual = 0
    hsr_segmentos_actuales = 0
    velocidad_anterior_hsr_sostenida = False

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
        velocidad = velocidad_confiable(velocidad_gps, velocidad_distancia)

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

        if abs(aceleracion) > ACELERACION_MAXIMA_REALISTA:
            segmentos_descartados += 1
            continue

        distancia += d
        duracion_seg += dt
        segmentos_validos += 1
        velocidades.append(velocidad)

        deceleracion_intensa = (
            aceleracion <= UMBRAL_DECELERACION
            and velocidad_anterior_valida is not None
            and velocidad_anterior_hsr_sostenida
        )

        if deceleracion_intensa:
            if not en_deceleracion:
                deceleraciones += 1
            en_deceleracion = True
        else:
            en_deceleracion = False

        if velocidad >= UMBRAL_HSR:
            hsr_distancia_actual += d
            hsr_segmentos_actuales += 1
        else:
            if hsr_segmentos_actuales >= 2:
                hsr += hsr_distancia_actual
            hsr_distancia_actual = 0
            hsr_segmentos_actuales = 0

        if velocidad >= UMBRAL_SPRINT:
            if not en_sprint:
                sprints += 1
            en_sprint = True
        else:
            en_sprint = False

        velocidad_anterior_valida = velocidad
        velocidad_anterior_hsr_sostenida = hsr_segmentos_actuales >= 2

    if hsr_segmentos_actuales >= 2:
        hsr += hsr_distancia_actual

    vmax = max(velocidades) if velocidades else 0
    if vmax < UMBRAL_HSR:
        hsr = 0
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
        "puntos_gps": puntos_originales,
        "puntos_metricas": len(gps),
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
