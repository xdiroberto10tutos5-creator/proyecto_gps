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

    def test_acepta_precision_moderada_de_celular(self):
        puntos = [
            punto(8.980000, -79.520000, 0, 0),
            punto(8.980100, -79.520000, 2, 5, precision=25),
        ]

        resultado = calcular_metricas_desde_puntos(puntos)

        self.assertGreater(resultado["distancia_metros"], 0)
        self.assertEqual(resultado["segmentos_validos"], 1)

    def test_caminata_no_cuenta_deceleracion_deportiva(self):
        puntos = [
            punto(8.980000, -79.520000, 0, 0),
            punto(8.980030, -79.520000, 3.5, 1),
            punto(8.980045, -79.520000, 1.0, 2),
        ]

        resultado = calcular_metricas_desde_puntos(puntos)

        self.assertEqual(resultado["deceleraciones"], 0)

    def test_sesion_quieta_no_acumula_drift_gps(self):
        puntos = [
            punto(8.980000, -79.520000, 0, 0),
            punto(8.980010, -79.520000, 1.2, 1),
            punto(8.980020, -79.520000, 1.1, 2),
        ]

        resultado = calcular_metricas_desde_puntos(puntos)

        self.assertEqual(resultado["distancia_metros"], 0)
        self.assertEqual(resultado["velocidad_max_kmh"], 0)

    def test_usuario_quieto_con_drift_gps_no_genera_metricas(self):
        puntos = [
            punto(8.980000, -79.520000, 0, 0, precision=12),
            punto(8.980015, -79.520006, 0.2, 3, precision=14),
            punto(8.979995, -79.520010, 0.3, 6, precision=13),
            punto(8.980012, -79.519996, 0.2, 9, precision=15),
        ]

        resultado = calcular_metricas_desde_puntos(puntos)

        self.assertEqual(resultado["distancia_metros"], 0)
        self.assertEqual(resultado["velocidad_max_kmh"], 0)
        self.assertEqual(resultado["hsr_metros"], 0)
        self.assertEqual(resultado["sprints"], 0)
        self.assertEqual(resultado["deceleraciones"], 0)

    def test_caminata_lenta_real_acumula_distancia_sin_hsr(self):
        puntos = [
            punto(8.980000, -79.520000, 0, 0),
            punto(8.980090, -79.520000, 1.2, 8),
            punto(8.980180, -79.520000, 1.2, 16),
        ]

        resultado = calcular_metricas_desde_puntos(puntos)

        self.assertGreater(resultado["distancia_metros"], 15)
        self.assertEqual(resultado["hsr_metros"], 0)
        self.assertEqual(resultado["sprints"], 0)
        self.assertEqual(resultado["deceleraciones"], 0)

    def test_salto_gps_imposible_se_descarta(self):
        puntos = [
            punto(8.980000, -79.520000, 0, 0),
            punto(8.985000, -79.520000, 60, 2),
        ]

        resultado = calcular_metricas_desde_puntos(puntos)

        self.assertEqual(resultado["distancia_metros"], 0)
        self.assertEqual(resultado["segmentos_descartados"], 1)

    def test_caminata_ida_y_vuelta_corta(self):
        puntos = [
            punto(8.980000, -79.520000, 0, 0),
            punto(8.980225, -79.520000, 1.4, 18),
            punto(8.980000, -79.520000, 1.4, 36),
        ]

        resultado = calcular_metricas_desde_puntos(puntos)

        self.assertGreater(resultado["distancia_metros"], 45)
        self.assertLess(resultado["distancia_metros"], 55)
        self.assertEqual(resultado["hsr_metros"], 0)
        self.assertEqual(resultado["deceleraciones"], 0)

    def test_caminata_recta_con_zigzag_gps_no_duplica_distancia(self):
        puntos = [
            punto(8.980000, -79.520000, 0, 0, precision=9),
            punto(8.980045, -79.519955, 1.1, 4, precision=10),
            punto(8.980090, -79.520045, 1.1, 8, precision=9),
            punto(8.980135, -79.519955, 1.1, 12, precision=10),
            punto(8.980180, -79.520045, 1.1, 16, precision=9),
            punto(8.980225, -79.520000, 1.1, 20, precision=9),
            punto(8.980180, -79.520045, 1.1, 24, precision=9),
            punto(8.980135, -79.519955, 1.1, 28, precision=10),
            punto(8.980090, -79.520045, 1.1, 32, precision=9),
            punto(8.980045, -79.519955, 1.1, 36, precision=10),
            punto(8.980000, -79.520000, 1.1, 40, precision=9),
        ]

        resultado = calcular_metricas_desde_puntos(puntos)

        self.assertGreater(resultado["distancia_metros"], 35)
        self.assertLess(resultado["distancia_metros"], 65)
        self.assertLess(resultado["puntos_metricas"], resultado["puntos_gps"])

    def test_caminata_con_speed_gps_falso_no_genera_hsr(self):
        puntos = [
            punto(8.980000, -79.520000, 0, 0, precision=8),
            punto(8.980030, -79.520000, 5.4, 4, precision=8),
            punto(8.980060, -79.520000, 5.2, 8, precision=8),
            punto(8.980090, -79.520000, 1.1, 12, precision=8),
        ]

        resultado = calcular_metricas_desde_puntos(puntos)

        self.assertEqual(resultado["hsr_metros"], 0)
        self.assertEqual(resultado["sprints"], 0)
        self.assertEqual(resultado["deceleraciones"], 0)
        self.assertLess(resultado["velocidad_max_kmh"], 10)

    def test_sprint_hsr_valido(self):
        puntos = [
            punto(8.980000, -79.520000, 0, 0),
            punto(8.980060, -79.520000, 4.7, 1),
            punto(8.980125, -79.520000, 6.0, 2),
        ]

        resultado = calcular_metricas_desde_puntos(puntos)

        self.assertGreater(resultado["hsr_metros"], 0)
        self.assertEqual(resultado["sprints"], 1)
        self.assertGreater(resultado["velocidad_max_kmh"], 20)


if __name__ == "__main__":
    unittest.main()
