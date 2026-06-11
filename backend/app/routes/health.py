from fastapi import APIRouter

from app.services.auth_service import obtener_estado_auth

router = APIRouter()


@router.get("/")
def health():

    return {
        "message": "API funcionando",
        "app": "/app",
        "dashboard": "/dashboard",
        "docs": "/docs"
    }


@router.get("/supabase")
def health_supabase():
    estado = obtener_estado_auth()

    return {
        "estado": "conectado",
        "servicio": "Supabase",
        "auth_habilitado": estado["auth_habilitado"],
        "esquema_rls_listo": estado["esquema_rls_listo"],
    }
