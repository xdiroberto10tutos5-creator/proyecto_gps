from fastapi import APIRouter

from app.supabase_client import get_gps_by_sesion, insert_metricas, get_metricas_by_sesion
from app.services.calculos import haversine

router = APIRouter()

@router.get("/sesion/{sesion_id}")
def metricas_sesion(sesion_id: str):

    gps = get_gps_by_sesion(sesion_id)

    distancia = 0
    hsr = 0
    sprints = 0
    aceleraciones = 0
    deceleraciones = 0

    velocidades = []

    umbral_hsr = 5.5      # 19.8 km/h
    umbral_sprint = 7.0  # 25.2 km/h

    for i in range(1, len(gps)):

        p1 = gps[i - 1]
        p2 = gps[i]

        precision = float(p2.get("precision_gps") or 0)

        if precision > 10:
            continue

        d = haversine(
            float(p1["latitud"]),
            float(p1["longitud"]),
            float(p2["latitud"]),
            float(p2["longitud"])
        )

        if d < 2:
            continue

        v = float(p2.get("velocidad") or 0)
        v_prev = float(p1.get("velocidad") or 0)

        if v < 0.5:
            v = 0

        ac = (v - v_prev) / 3

        distancia += d
        velocidades.append(v)

        if ac >= 2:
            aceleraciones += 1

        if ac <= -2:
            deceleraciones += 1

        if v >= umbral_hsr:
            hsr += d

        if v >= umbral_sprint:
            sprints += 1

    vmax = max(velocidades) if velocidades else 0

    vprom = (
        sum(velocidades) / len(velocidades)
    ) if velocidades else 0

    duracion_min = len(gps) * 3 / 60

    dist_min = (
        distancia / duracion_min
    ) if duracion_min > 0 else 0

    carga_fisica = (
        distancia * 0.30
        + hsr * 0.25
        + sprints * 10
        + aceleraciones * 5
        + deceleraciones * 5
    )

    return {
        "distancia_metros": round(distancia, 2),
        "velocidad_max_ms": round(vmax, 2),
        "velocidad_max_kmh": round(vmax * 3.6, 2),
        "velocidad_promedio_ms": round(vprom, 2),
        "velocidad_promedio_kmh": round(vprom * 3.6, 2),
        "hsr_metros": round(hsr, 2),
        "sprints": sprints,
        "aceleraciones": aceleraciones,
        "deceleraciones": deceleraciones,
        "distancia_por_minuto": round(dist_min, 2),
        "carga_fisica": round(carga_fisica, 2),
        "puntos_gps": len(gps)
    }
    
@router.post("/guardar/{sesion_id}/{jugador_id}")
def guardar_metricas(sesion_id: str, jugador_id: str):

    resultado = metricas_sesion(sesion_id)

    data = {
        "sesion_id": sesion_id,
        "jugador_id": jugador_id,
        "distancia_total": resultado["distancia_metros"],
        "velocidad_max": resultado["velocidad_max_kmh"],
        "velocidad_promedio": resultado["velocidad_promedio_kmh"],
        "hsr": resultado["hsr_metros"],
        "sprints": resultado["sprints"],
        "aceleraciones": resultado["aceleraciones"],
        "deceleraciones": resultado["deceleraciones"],
        "dist_min": resultado["distancia_por_minuto"],
        "carga_fisica": resultado["carga_fisica"],
        "score_actual": 0
    }

    guardado = insert_metricas(data)

    return {
        "estado": "metricas_guardadas",
        "metricas": guardado
    }

@router.get("/guardadas/{sesion_id}")
def obtener_metricas_guardadas(sesion_id: str):

    datos = get_metricas_by_sesion(sesion_id)

    return {
        "total": len(datos),
        "data": datos
    }