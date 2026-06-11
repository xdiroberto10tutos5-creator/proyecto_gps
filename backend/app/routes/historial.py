from fastapi import APIRouter

from app.services.authorization_service import requerir_jugador_propio
from app.supabase_client import get_metricas_by_jugador

router = APIRouter()

@router.get("/jugador/{jugador_id}")
def historial_jugador(jugador_id: str):
    requerir_jugador_propio(jugador_id)
    metricas = get_metricas_by_jugador(jugador_id)

    historial = []

    for m in metricas:
        historial.append({
            "sesion_id": m.get("sesion_id"),
            "distancia_total": m.get("distancia_total"),
            "velocidad_max": m.get("velocidad_max"),
            "hsr": m.get("hsr"),
            "sprints": m.get("sprints"),
            "deceleraciones": m.get("deceleraciones"),
            "dist_min": m.get("dist_min")
        })

    return {
        "jugador_id": jugador_id,
        "total_sesiones": len(historial),
        "historial": historial
    }
