from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.security_context import get_auth_user
from app.services.auth_service import obtener_coach_actual
from app.supabase_client import get_data, insert_data, update_data

router = APIRouter()

class Coach(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    email: str | None = None


@router.get("/")
def listar_coaches():
    user = get_auth_user()
    return {
        "data": get_data("coaches", "user_id", user["id"])
    }


@router.post("/")
def crear_coach(data: Coach):
    user = get_auth_user()
    existentes = get_data("coaches", "user_id", user["id"])
    perfil = {
        "nombre": data.nombre.strip(),
        "email": data.email or user.get("email"),
        "user_id": user["id"],
    }

    if existentes:
        return update_data("coaches", perfil, "id", existentes[0]["id"])
    return insert_data("coaches", perfil)


@router.delete("/{coach_id}")
def eliminar_coach(coach_id: str):
    obtener_coach_actual()
    raise HTTPException(
        status_code=403,
        detail="La eliminación de cuenta requiere un flujo administrativo seguro"
    )
