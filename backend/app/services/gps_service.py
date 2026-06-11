from datetime import datetime, timezone

from fastapi import HTTPException

from app.services.authorization_service import requerir_sesion_y_jugador
from app.services.metricas_service import guardar_metricas_calculadas
from app.supabase_client import (
    get_gps_by_sesion,
    get_gps_by_sesion_jugador,
    insert_data
)

MIN_PUNTOS_LOTE = 2


def timestamp_actual():
    return datetime.now(timezone.utc).isoformat()


def preparar_puntos_lote(data):
    puntos_insertar = []

    for punto in data.puntos:
        puntos_insertar.append({
            "sesion_id": data.sesion_id,
            "jugador_id": data.jugador_id,
            "latitud": punto.latitud,
            "longitud": punto.longitud,
            "velocidad": punto.velocidad,
            "precision_gps": punto.precision_gps,
            "timestamp": punto.timestamp or timestamp_actual()
        })

    return puntos_insertar


def guardar_lote_gps(data):
    if len(data.puntos) < MIN_PUNTOS_LOTE:
        raise HTTPException(
            status_code=400,
            detail=f"Se requieren al menos {MIN_PUNTOS_LOTE} puntos GPS para calcular métricas"
        )

    requerir_sesion_y_jugador(data.sesion_id, data.jugador_id)
    puntos_insertar = preparar_puntos_lote(data)
    resultado_gps = insert_data("gps_data", puntos_insertar)
    resultado_metricas = guardar_metricas_calculadas(data.sesion_id, data.jugador_id)

    return {
        "estado": "lote_guardado_y_metricas_calculadas",
        "puntos_recibidos": len(data.puntos),
        "gps": resultado_gps,
        "metricas": resultado_metricas["guardadas"],
        "resumen_calculo": resultado_metricas["calculadas"]
    }


def obtener_gps_sesion(sesion_id, jugador_id=None):
    if jugador_id:
        requerir_sesion_y_jugador(sesion_id, jugador_id)
    else:
        from app.services.authorization_service import requerir_sesion_propia
        requerir_sesion_propia(sesion_id)

    if jugador_id:
        datos = get_gps_by_sesion_jugador(sesion_id, jugador_id)
    else:
        datos = get_gps_by_sesion(sesion_id)

    return {
        "total": len(datos),
        "data": datos
    }
