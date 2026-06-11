import unittest
from datetime import datetime, timedelta, timezone

from app.services.metricas_service import calcular_metricas_desde_puntos


def punto(latitud, longitud, velocidad, segundos, precision=5):
    inicio = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return {
        "latitud": latitud,
        "longitud": longitud,
        "velocidad": velocidad,
        "precision_gps": precision,
        "timestamp": (inicio + timedelta(seconds=segundos)).isoformat(),
    }


class MetricasTests(unittest.TestCase):
    def test_calcula_las_seis_metricas_principales(self):
        puntos = [
            punto(8.980000, -79.520000, 0, 0),
            punto(8.980045, -79.520000, 4.8, 1),
            punto(8.980100, -79.520000, 6.1, 2),
            punto(8.980145, -79.520000, 3.5, 3),
        ]

        resultado = calcular_metricas_desde_puntos(puntos)

        self.assertGreater(resultado["distancia_metros"], 0)
        self.assertEqual(resultado["velocidad_max_kmh"], 21.96)
        self.assertGreater(resultado["hsr_metros"], 0)
        self.assertEqual(resultado["sprints"], 1)
        self.assertEqual(resultado["deceleraciones"], 1)
        self.assertGreater(resultado["distancia_por_minuto"], 0)

    def test_descarta_segmentos_con_mala_precision(self):
        puntos = [
            punto(8.980000, -79.520000, 0, 0),
            punto(8.980100, -79.520000, 6, 2, precision=40),
        ]

        resultado = calcular_metricas_desde_puntos(puntos)

        self.assertEqual(resultado["distancia_metros"], 0)
        self.assertEqual(resultado["segmentos_descartados"], 1)


if __name__ == "__main__":
    unittest.main()
