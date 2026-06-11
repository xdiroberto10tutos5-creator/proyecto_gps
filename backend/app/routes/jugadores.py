from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.auth_service import obtener_coach_actual
from app.services.authorization_service import requerir_jugador_propio
from app.supabase_client import delete_data, get_data, insert_data

router = APIRouter()


class JugadorCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    posicion: str | None = Field(default=None, max_length=60)
    edad: int | None = Field(default=None, ge=14, le=18)
    numero: int | None = Field(default=None, ge=0, le=99)
    equipo_id: str | None = None


@router.get("/")
def listar_jugadores():
    coach = obtener_coach_actual()
    return {
        "data": get_data("jugadores", "coach_id", coach["id"])
    }


@router.post("/")
def crear_jugador(data: JugadorCreate):
    coach = obtener_coach_actual()
    jugador = {
        "nombre": data.nombre.strip(),
        "posicion": data.posicion.strip() if data.posicion else None,
        "edad": data.edad,
        "numero": data.numero,
        "equipo_id": data.equipo_id,
        "coach_id": coach["id"],
    }

    resultado = insert_data("jugadores", jugador)

    return resultado


@router.delete("/{jugador_id}")
def eliminar_jugador(jugador_id: str):
    requerir_jugador_propio(jugador_id)
    resultado = delete_data("jugadores", "id", jugador_id)

    return {
        "estado": "jugador_eliminado",
        "data": resultado
    }
