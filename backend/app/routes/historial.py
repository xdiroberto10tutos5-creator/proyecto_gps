from fastapi import APIRouter

from app.supabase_client import get_metricas_by_jugador

router = APIRouter()

@router.get("/jugador/{jugador_id}")
def historial_jugador(jugador_id: str):

    metricas = get_metricas_by_jugador(jugador_id)

    historial = []

    for m in metricas:
        historial.append({
            "sesion_id": m.get("sesion_id"),
            "distancia_total": m.get("distancia_total"),
            "velocidad_max": m.get("velocidad_max"),
            "velocidad_promedio": m.get("velocidad_promedio"),
            "hsr": m.get("hsr"),
            "sprints": m.get("sprints"),
            "carga_fisica": m.get("carga_fisica"),
            "score_actual": m.get("score_actual")
        })

    return {
        "jugador_id": jugador_id,
        "total_sesiones": len(historial),
        "historial": historial
    }