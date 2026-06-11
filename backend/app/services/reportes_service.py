from datetime import datetime, timezone

from app.services.metricas_service import obtener_metricas_guardadas, obtener_perfil_calculo
from app.services.authorization_service import (
    requerir_sesion_propia,
    requerir_sesion_y_jugador
)
from app.supabase_client import get_data


def generar_analisis_metricas(metrica):
    distancia = float(metrica.get("distancia_total") or 0)
    velocidad_max = float(metrica.get("velocidad_max") or 0)
    hsr = float(metrica.get("hsr") or 0)
    sprints = int(metrica.get("sprints") or 0)
    deceleraciones = int(metrica.get("deceleraciones") or 0)
    dist_min = float(metrica.get("dist_min") or 0)

    if distancia == 0:
        conclusion = "No hay carga GPS suficiente para interpretar la sesión."
    elif velocidad_max >= 20.9 or sprints >= 3:
        conclusion = "Sesión con acciones de alta intensidad."
    elif hsr > 0 or dist_min >= 65:
        conclusion = "Sesión con esfuerzo físico moderado."
    else:
        conclusion = "Sesión de baja intensidad o calentamiento."

    if deceleraciones >= 6:
        recomendacion = "Revisar cambios de ritmo y recuperación posterior."
    elif hsr >= distancia * 0.20 and distancia > 0:
        recomendacion = "Buen volumen de carrera rápida para analizar por posición."
    else:
        recomendacion = "Comparar con próximas sesiones para ver tendencia."

    return {
        "resumen": {
            "distancia_total": distancia,
            "velocidad_max": velocidad_max,
            "hsr": hsr,
            "sprints": sprints,
            "deceleraciones": deceleraciones,
            "dist_min": dist_min
        },
        "analisis": {
            "conclusion": conclusion,
            "recomendacion": recomendacion
        },
        "perfil_calculo": obtener_perfil_calculo()
    }


def generar_reporte_sesion(sesion_id, jugador_id=None):
    if jugador_id:
        requerir_sesion_y_jugador(sesion_id, jugador_id)
    else:
        requerir_sesion_propia(sesion_id)
    metricas = obtener_metricas_guardadas(sesion_id, jugador_id)

    if len(metricas) == 0:
        return {
            "error": "No hay métricas guardadas para esta sesión"
        }

    metrica = metricas[-1]
    analisis = generar_analisis_metricas(metrica)
    jugador_id = metrica.get("jugador_id") or jugador_id
    sesiones = get_data("sesiones", "id", sesion_id)
    jugadores = get_data("jugadores", "id", jugador_id) if jugador_id else []

    return {
        "sesion_id": sesion_id,
        "jugador_id": jugador_id,
        "sesion": sesiones[0] if sesiones else {"id": sesion_id},
        "jugador": jugadores[0] if jugadores else {"id": jugador_id},
        "generado_en": datetime.now(timezone.utc).isoformat(),
        **analisis
    }
