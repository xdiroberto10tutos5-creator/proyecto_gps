import os
from dotenv import load_dotenv

load_dotenv()


def _lista_entorno(nombre, valor_default=""):
    valor = os.getenv(nombre, valor_default)
    return [item.strip() for item in valor.split(",") if item.strip()]


ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", SUPABASE_KEY)
CORS_ORIGINS = _lista_entorno(
    "CORS_ORIGINS",
    "*" if ENVIRONMENT == "development" else ""
)
DOCS_ENABLED = os.getenv("DOCS_ENABLED", "true").lower() == "true"
COOKIE_SECURE = ENVIRONMENT == "production"
