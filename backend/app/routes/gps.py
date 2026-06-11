from fastapi import APIRouter
from typing import List
from pydantic import BaseModel, Field

from app.services.gps_service import (
    guardar_lote_gps as guardar_lote_gps_service,
    obtener_gps_sesion as obtener_gps_sesion_service
)

router = APIRouter()


class PuntoGPS(BaseModel):
    sesion_id: str | None = None
    jugador_id: str | None = None
    latitud: float = Field(ge=-90, le=90)
    longitud: float = Field(ge=-180, le=180)
    velocidad: float = Field(default=0, ge=0)
    precision_gps: float = Field(default=0, ge=0)
    timestamp: str | None = None


class GPSLote(BaseModel):
    sesion_id: str
    jugador_id: str
    puntos: List[PuntoGPS] = Field(min_length=2, max_length=20000)


@router.post("/lote")
def guardar_lote_gps(data: GPSLote):

    return guardar_lote_gps_service(data)


@router.get("/sesion/{sesion_id}")
def obtener_gps_sesion(sesion_id: str, jugador_id: str | None = None):

    return obtener_gps_sesion_service(sesion_id, jugador_id)
