from fastapi import APIRouter

from app.supabase_client import get_metricas_by_sesion

router = APIRouter()

@router.get("/sesion/{sesion_id}")
def reporte_sesion(sesion_id: str):

    metricas = get_metricas_by_sesion(sesion_id)

    if len(metricas) == 0:
        return {
            "error": "No hay métricas guardadas para esta sesión"
        }

    m = metricas[-1]

    score = m.get("score_actual") or 0
    carga = m.get("carga_fisica") or 0

    if score >= 85:
        conclusion = "Rendimiento excelente."
    elif score >= 70:
        conclusion = "Buen rendimiento físico."
    elif score >= 50:
        conclusion = "Rendimiento medio, puede mejorar."
    else:
        conclusion = "Rendimiento bajo o poca actividad registrada."

    if carga >= 700:
        recomendacion = "Carga física alta. Se recomienda recuperación."
    elif carga >= 400:
        recomendacion = "Carga física moderada."
    else:
        recomendacion = "Carga física baja."

    return {
        "sesion_id": sesion_id,
        "resumen": {
            "distancia_total": m.get("distancia_total"),
            "velocidad_max": m.get("velocidad_max"),
            "velocidad_promedio": m.get("velocidad_promedio"),
            "hsr": m.get("hsr"),
            "sprints": m.get("sprints"),
            "aceleraciones": m.get("aceleraciones"),
            "deceleraciones": m.get("deceleraciones"),
            "dist_min": m.get("dist_min"),
            "carga_fisica": carga,
            "score_actual": score
        },
        "analisis": {
            "conclusion": conclusion,
            "recomendacion": recomendacion
        }
    }