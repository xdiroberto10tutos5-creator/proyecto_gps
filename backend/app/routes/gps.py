from fastapi import APIRouter
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.supabase_client import insert_data, get_gps_by_sesion, insert_metricas
from app.routes.metricas import metricas_sesion

router = APIRouter()


class GPSData(BaseModel):
    sesion_id: str
    jugador_id: str
    latitud: float
    longitud: float
    velocidad: float = 0
    precision_gps: float = 0


class PuntoGPS(BaseModel):
    sesion_id: str
    jugador_id: str
    latitud: float
    longitud: float
    velocidad: float = 0
    precision_gps: float = 0
    timestamp: str | None = None


class GPSLote(BaseModel):
    sesion_id: str
    jugador_id: str
    puntos: List[PuntoGPS]


@router.post("/")
def guardar_gps(data: GPSData):

    gps = {
        "sesion_id": data.sesion_id,
        "jugador_id": data.jugador_id,
        "latitud": data.latitud,
        "longitud": data.longitud,
        "velocidad": data.velocidad,
        "precision_gps": data.precision_gps,
        "timestamp": datetime.utcnow().isoformat()
    }

    resultado = insert_data("gps_data", gps)

    return {
        "estado": "guardado",
        "data": resultado
    }


@router.post("/lote")
def guardar_lote_gps(data: GPSLote):

    puntos_insertar = []

    for punto in data.puntos:
        puntos_insertar.append({
            "sesion_id": data.sesion_id,
            "jugador_id": data.jugador_id,
            "latitud": punto.latitud,
            "longitud": punto.longitud,
            "velocidad": punto.velocidad,
            "precision_gps": punto.precision_gps,
            "timestamp": punto.timestamp or datetime.utcnow().isoformat()
        })

    resultado_gps = insert_data(
        "gps_data",
        puntos_insertar
    )

    resultado_metricas = metricas_sesion(data.sesion_id)

    metricas_guardar = {
        "sesion_id": data.sesion_id,
        "jugador_id": data.jugador_id,
        "distancia_total": resultado_metricas["distancia_metros"],
        "velocidad_max": resultado_metricas["velocidad_max_kmh"],
        "velocidad_promedio": resultado_metricas["velocidad_promedio_kmh"],
        "hsr": resultado_metricas["hsr_metros"],
        "sprints": resultado_metricas["sprints"],
        "aceleraciones": resultado_metricas["aceleraciones"],
        "deceleraciones": resultado_metricas["deceleraciones"],
        "dist_min": resultado_metricas["distancia_por_minuto"],
        "carga_fisica": resultado_metricas["carga_fisica"],
        "score_actual": resultado_metricas["score_actual"]
    }

    resultado_guardado_metricas = insert_metricas(
        metricas_guardar
    )

    return {
        "estado": "lote_guardado_y_metricas_calculadas",
        "puntos_recibidos": len(data.puntos),
        "gps": resultado_gps,
        "metricas": resultado_guardado_metricas
    }

    puntos_insertar = []

    for punto in data.puntos:
        puntos_insertar.append({
            "sesion_id": data.sesion_id,
            "jugador_id": data.jugador_id,
            "latitud": punto.latitud,
            "longitud": punto.longitud,
            "velocidad": punto.velocidad,
            "precision_gps": punto.precision_gps,
            "timestamp": punto.timestamp or datetime.utcnow().isoformat()
        })

    resultado = insert_data("gps_data", puntos_insertar)

    return {
        "estado": "lote_guardado",
        "puntos_recibidos": len(data.puntos),
        "data": resultado
    }


@router.get("/sesion/{sesion_id}")
def obtener_gps_sesion(sesion_id: str):

    datos = get_gps_by_sesion(sesion_id)

    return {
        "total": len(datos),
        "data": datos
    }