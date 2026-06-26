from datetime import datetime, timedelta, timezone
import math

from fastapi import APIRouter

from app.services.metricas_service import (
    calcular_metricas_desde_puntos,
    construir_metricas_guardar,
)
from app.services.reportes_service import generar_analisis_metricas

router = APIRouter()

CANCHA_SUPERFICIE_M2 = 4700.08
CANCHA_PERIMETRO_M = 288.07
CANCHA_LARGO_M = 94.07289177276158
CANCHA_ANCHO_M = 49.96210822723841


def _timestamp(base, seconds):
    return (base + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def _generar_puntos_demo():
    """Genera un recorrido sintético sobre la cancha configurada para la demo."""
    base_time = datetime(2026, 6, 10, 15, 30, tzinfo=timezone.utc)
    base_lat = 9.035833
    base_lon = -79.469444
    metros_por_grado_lat = 111_320
    metros_por_grado_lon = 111_320 * math.cos(math.radians(base_lat))
    puntos = []

    for i in range(128):
        # Recorrido continuo con mayor presencia en la mitad inferior del campo.
        x_m = CANCHA_LARGO_M / 2 + (CANCHA_LARGO_M / 2 - 3) * math.sin(i * 0.21)
        y_m = 16 + 10 * math.sin(i * 0.13) + 6 * math.sin(i * 0.47)
        if i % 23 in (18, 19, 20):
            y_m += 17

        x_m = max(2, min(CANCHA_LARGO_M - 2, x_m))
        y_m = max(2, min(CANCHA_ANCHO_M - 2, y_m))
        lat = base_lat + (x_m - CANCHA_LARGO_M / 2) / metros_por_grado_lat
        lon = base_lon + (y_m - CANCHA_ANCHO_M / 2) / metros_por_grado_lon

        # Variación mínima para imitar la imprecisión normal del teléfono.
        lat += math.sin(i * 0.85) * 0.000006
        lon += math.cos(i * 0.61) * 0.000006

        if i % 24 in (8, 9, 10, 11):
            velocidad = 7.4 + (i % 3) * 0.35
        elif i % 14 in (4, 5, 6):
            velocidad = 5.8
        else:
            velocidad = 2.8 + (i % 5) * 0.45

        if i % 28 == 0 and i > 0:
            velocidad = 1.0

        puntos.append({
            "id": f"demo-gps-{i + 1}",
            "sesion_id": "demo-sesion",
            "jugador_id": "demo-jugador",
            "latitud": round(lat, 7),
            "longitud": round(lon, 7),
            "velocidad": round(velocidad, 2),
            "precision_gps": 5 + (i % 4),
            "timestamp": _timestamp(base_time, i * 4),
        })

    return puntos


def _historial_demo(metrica_actual):
    base = [
        ("Sesión técnica", 1460, 22.8, 180, 2, 5, 72),
        ("Interválico corto", 1725, 25.4, 310, 5, 8, 86),
        ("Reducido 6v6", 1588, 24.1, 245, 4, 7, 79),
        ("Transiciones", 1890, 27.6, 420, 7, 10, 94),
    ]
    historial = []

    for i, (nombre, distancia, velocidad, hsr, sprints, decel, dist_min) in enumerate(base, start=1):
        historial.append({
            "sesion_id": f"demo-hist-{i}",
            "sesion_nombre": nombre,
            "jugador_id": "demo-jugador",
            "distancia_total": distancia,
            "velocidad_max": velocidad,
            "hsr": hsr,
            "sprints": sprints,
            "deceleraciones": decel,
            "dist_min": dist_min,
        })

    historial.append({
        "sesion_id": "demo-sesion",
        "sesion_nombre": "Demo GPS actual",
        "jugador_id": "demo-jugador",
        **metrica_actual,
    })
    return historial


@router.get("/sesion")
def obtener_sesion_demo():
    puntos = _generar_puntos_demo()
    calculadas = calcular_metricas_desde_puntos(puntos)
    metricas = construir_metricas_guardar("demo-sesion", "demo-jugador", calculadas)
    historial = _historial_demo(metricas)
    reporte = generar_analisis_metricas(metricas)

    return {
        "mensaje": "Datos simulados generados localmente. No se guardaron en Supabase.",
        "coach": {
            "id": "demo-coach",
            "nombre": "Coach Demo",
            "email": "coach.demo@example.com",
        },
        "jugador": {
            "id": "demo-jugador",
            "nombre": "Jugador Demo",
            "posicion": "Extremo",
            "edad": 21,
            "numero": 11,
            "equipo_id": "Equipo Demo",
        },
        "sesion": {
            "id": "demo-sesion",
            "nombre": "Demo GPS actual",
            "estado": "finalizada",
            "coach_id": "demo-coach",
        },
        "cancha": {
            "estadio": "Cancha del Colegio San Agustín",
            "superficie_m2": CANCHA_SUPERFICIE_M2,
            "perimetro_m": CANCHA_PERIMETRO_M,
            "largo_m": round(CANCHA_LARGO_M, 2),
            "ancho_m": round(CANCHA_ANCHO_M, 2),
        },
        "gps": {
            "total": len(puntos),
            "data": puntos,
        },
        "metricas": {
            "total": 1,
            "data": [metricas],
            "calculadas": calculadas,
        },
        "historial": {
            "jugador_id": "demo-jugador",
            "total_sesiones": len(historial),
            "historial": historial,
        },
        "reporte": {
            "sesion_id": "demo-sesion",
            "jugador_id": "demo-jugador",
            **reporte,
        },
    }
