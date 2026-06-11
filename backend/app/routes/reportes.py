from fastapi import APIRouter

from app.services.reportes_service import generar_reporte_sesion

router = APIRouter()

@router.get("/sesion/{sesion_id}")
def reporte_sesion(sesion_id: str, jugador_id: str | None = None):

    return generar_reporte_sesion(sesion_id, jugador_id)
