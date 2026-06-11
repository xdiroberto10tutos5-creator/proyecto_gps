from fastapi import HTTPException

from app.services.auth_service import obtener_coach_actual
from app.supabase_client import get_data


def _requerir_recurso(tabla, recurso_id, coach_id):
    recursos = get_data(tabla, "id", recurso_id)
    if not recursos or recursos[0].get("coach_id") != coach_id:
        raise HTTPException(
            status_code=404,
            detail="Recurso no encontrado para el coach autenticado"
        )
    return recursos[0]


def requerir_jugador_propio(jugador_id):
    coach = obtener_coach_actual()
    return _requerir_recurso("jugadores", jugador_id, coach["id"])


def requerir_sesion_propia(sesion_id):
    coach = obtener_coach_actual()
    return _requerir_recurso("sesiones", sesion_id, coach["id"])


def requerir_sesion_y_jugador(sesion_id, jugador_id):
    return (
        requerir_sesion_propia(sesion_id),
        requerir_jugador_propio(jugador_id),
    )
