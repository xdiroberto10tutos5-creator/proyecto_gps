from fastapi import APIRouter
from pydantic import BaseModel
from app.supabase_client import supabase

router = APIRouter()

class SesionCreate(BaseModel):
    nombre: str
    coach_id: str
    equipo_id: str | None = None

@router.post("/")
def crear_sesion(data: SesionCreate):
    result = supabase.table("sesiones").insert({
        "nombre": data.nombre,
        "coach_id": data.coach_id,
        "equipo_id": data.equipo_id,
        "estado": "programada"
    }).execute()

    return result.data

@router.post("/{sesion_id}/iniciar")
def iniciar_sesion(sesion_id: str):
    result = supabase.table("sesiones").update({
        "estado": "activa"
    }).eq("id", sesion_id).execute()

    return result.data

@router.post("/{sesion_id}/finalizar")
def finalizar_sesion(sesion_id: str):
    result = supabase.table("sesiones").update({
        "estado": "finalizada"
    }).eq("id", sesion_id).execute()

    return result.data