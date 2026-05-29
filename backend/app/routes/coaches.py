from fastapi import APIRouter
from pydantic import BaseModel

from app.supabase_client import insert_data

router = APIRouter()

class Coach(BaseModel):
    nombre: str
    email: str

@router.post("/")
def crear_coach(data: Coach):

    coach = {
        "nombre": data.nombre,
        "email": data.email
    }

    resultado = insert_data(
        "coaches",
        coach
    )

    return resultado