import unittest
from unittest.mock import patch

from app.services import auth_service


class AuthCacheTests(unittest.TestCase):
    def setUp(self):
        auth_service._token_cache.clear()

    def test_validar_token_reutiliza_cache(self):
        with patch.object(
            auth_service,
            "_auth_request",
            return_value={"id": "usuario-prueba"},
        ) as auth_request:
            self.assertEqual(
                auth_service.validar_token("token-prueba")["id"],
                "usuario-prueba",
            )
            self.assertEqual(
                auth_service.validar_token("token-prueba")["id"],
                "usuario-prueba",
            )

        self.assertEqual(auth_request.call_count, 1)
        auth_service.invalidar_token_cache("token-prueba")
        self.assertNotIn("token-prueba", auth_service._token_cache)


if __name__ == "__main__":
    unittest.main()
