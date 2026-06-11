from fastapi import APIRouter

from app.services.metricas_service import (
    calcular_metricas_sesion,
    guardar_metricas_calculadas,
    obtener_metricas_guardadas as obtener_metricas_guardadas_service,
    obtener_perfil_calculo
)
from app.services.authorization_service import (
    requerir_sesion_propia,
    requerir_sesion_y_jugador
)

router = APIRouter()


@router.get("/perfil")
def perfil_metricas():
    return obtener_perfil_calculo()


@router.get("/sesion/{sesion_id}")
def metricas_sesion(sesion_id: str, jugador_id: str | None = None):
    if jugador_id:
        requerir_sesion_y_jugador(sesion_id, jugador_id)
    else:
        requerir_sesion_propia(sesion_id)
    return calcular_metricas_sesion(sesion_id, jugador_id)
    
@router.post("/guardar/{sesion_id}/{jugador_id}")
def guardar_metricas(sesion_id: str, jugador_id: str):
    requerir_sesion_y_jugador(sesion_id, jugador_id)
    return {
        "estado": "metricas_guardadas",
        "metricas": guardar_metricas_calculadas(sesion_id, jugador_id)
    }

@router.get("/guardadas/{sesion_id}")
def obtener_metricas_guardadas(sesion_id: str, jugador_id: str | None = None):
    if jugador_id:
        requerir_sesion_y_jugador(sesion_id, jugador_id)
    else:
        requerir_sesion_propia(sesion_id)
    datos = obtener_metricas_guardadas_service(sesion_id, jugador_id)

    return {
        "total": len(datos),
        "data": datos
    }
