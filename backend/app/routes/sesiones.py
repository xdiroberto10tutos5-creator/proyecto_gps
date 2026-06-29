from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.auth_service import obtener_coach_actual
from app.services.authorization_service import requerir_sesion_propia
from app.supabase_client import (
    delete_data,
    delete_gps_by_sesion,
    delete_metricas_by_sesion,
    get_data,
    insert_data,
    update_data,
)

router = APIRouter()

class SesionCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    equipo_id: str | None = None


class SesionEstado(BaseModel):
    estado: str = Field(min_length=5, max_length=20)


@router.get("/")
def listar_sesiones():
    coach = obtener_coach_actual()
    return {
        "data": get_data("sesiones", "coach_id", coach["id"])
    }


@router.post("/")
def crear_sesion(data: SesionCreate):
    coach = obtener_coach_actual()
    result = insert_data("sesiones", {
        "nombre": data.nombre.strip(),
        "coach_id": coach["id"],
        "equipo_id": data.equipo_id,
        "estado": "programada"
    })

    return result


@router.delete("/{sesion_id}")
def eliminar_sesion(sesion_id: str):
    requerir_sesion_propia(sesion_id)
    gps_borrados = delete_gps_by_sesion(sesion_id)
    metricas_borradas = delete_metricas_by_sesion(sesion_id)
    result = delete_data("sesiones", "id", sesion_id)

    return {
        "estado": "sesion_eliminada",
        "gps_borrados": len(gps_borrados),
        "metricas_borradas": len(metricas_borradas),
        "data": result
    }


@router.patch("/{sesion_id}/estado")
def cambiar_estado_sesion(sesion_id: str, data: SesionEstado):
    requerir_sesion_propia(sesion_id)
    estados_validos = {"programada", "activa", "finalizada"}
    estado = data.estado.lower()

    if estado not in estados_validos:
        raise HTTPException(
            status_code=422,
            detail={
                "mensaje": "Estado inválido",
                "estados_validos": sorted(estados_validos)
            }
        )

    result = update_data("sesiones", {
        "estado": estado
    }, "id", sesion_id)

    return result

@router.post("/{sesion_id}/iniciar")
def iniciar_sesion(sesion_id: str):
    requerir_sesion_propia(sesion_id)
    result = update_data("sesiones", {
        "estado": "activa"
    }, "id", sesion_id)

    return result

@router.post("/{sesion_id}/finalizar")
def finalizar_sesion(sesion_id: str):
    requerir_sesion_propia(sesion_id)
    result = update_data("sesiones", {
        "estado": "finalizada"
    }, "id", sesion_id)

    return result
