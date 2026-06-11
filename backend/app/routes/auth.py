from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Cookie, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.security_context import (
    get_auth_user,
    reset_security_context,
    set_security_context,
)
from app.services.auth_service import (
    cerrar_sesion_supabase,
    guardar_token_cache,
    invalidar_token_cache,
    iniciar_sesion,
    obtener_coach_actual,
    obtener_estado_auth,
    registrar_coach,
    reenviar_confirmacion,
    renovar_sesion,
    validar_token,
)

router = APIRouter()
from app.config import COOKIE_SECURE
AUTH_CALLBACK_FILE = Path(__file__).resolve().parent.parent / "auth_callback.html"


class RegistroCoach(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)


class LoginCoach(BaseModel):
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)


class RefreshSession(BaseModel):
    refresh_token: str | None = Field(default=None, min_length=20)


class CompleteSession(BaseModel):
    access_token: str = Field(min_length=20)
    refresh_token: str = Field(min_length=20)
    expires_in: int = Field(default=3600, ge=60)


class ResendConfirmation(BaseModel):
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _guardar_cookies(response, data):
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    if not access_token or not refresh_token:
        return

    response.set_cookie(
        "gps_access_token",
        access_token,
        max_age=int(data.get("expires_in") or 3600),
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        "gps_refresh_token",
        refresh_token,
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/auth",
    )


def _respuesta_sesion(data):
    return {
        "autenticado": bool(data.get("access_token")),
        "expires_in": data.get("expires_in"),
        "user": data.get("user"),
        "coach": data.get("coach"),
    }


def _agregar_coach_a_sesion(data):
    access_token = data.get("access_token")
    user = data.get("user")
    if not access_token or not user:
        return data

    guardar_token_cache(access_token, user)
    context_tokens = set_security_context(access_token, user)
    try:
        return {**data, "coach": obtener_coach_actual()}
    finally:
        reset_security_context(context_tokens)


@router.post("/signup")
def signup(data: RegistroCoach, response: Response, request: Request):
    redirect_to = f"{str(request.base_url).rstrip('/')}/auth/callback"
    resultado = registrar_coach(
        data.nombre.strip(),
        data.email,
        data.password,
        redirect_to=redirect_to,
    )
    resultado = _agregar_coach_a_sesion(resultado)
    _guardar_cookies(response, resultado)
    return {
        **_respuesta_sesion(resultado),
        "confirmacion_url": redirect_to,
    }


@router.get("/callback", include_in_schema=False)
def callback():
    return FileResponse(AUTH_CALLBACK_FILE)


@router.post("/complete")
def complete(data: CompleteSession, response: Response):
    validar_token(data.access_token)
    resultado = data.model_dump()
    _guardar_cookies(response, resultado)
    return {"autenticado": True}


@router.get("/status")
def status():
    return obtener_estado_auth()


@router.post("/login")
def login(data: LoginCoach, response: Response):
    resultado = iniciar_sesion(data.email, data.password)
    resultado = _agregar_coach_a_sesion(resultado)
    _guardar_cookies(response, resultado)
    return _respuesta_sesion(resultado)


@router.post("/resend")
def resend(data: ResendConfirmation, request: Request):
    redirect_to = f"{str(request.base_url).rstrip('/')}/auth/callback"
    reenviar_confirmacion(data.email, redirect_to=redirect_to)
    return {
        "estado": "confirmacion_reenviada",
        "mensaje": "Revisa tu correo y la carpeta de spam.",
    }


@router.post("/refresh")
def refresh(
    response: Response,
    data: RefreshSession | None = None,
    gps_refresh_token: str | None = Cookie(default=None),
):
    refresh_token = (data.refresh_token if data else None) or gps_refresh_token
    if not refresh_token:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="No hay sesión para renovar")
    resultado = renovar_sesion(refresh_token)
    _guardar_cookies(response, resultado)
    return _respuesta_sesion(resultado)


@router.get("/me")
def me():
    return {
        "user": get_auth_user(),
        "coach": obtener_coach_actual(),
    }


@router.post("/logout")
def logout(
    response: Response,
    background_tasks: BackgroundTasks,
    gps_access_token: str | None = Cookie(default=None),
):
    invalidar_token_cache(gps_access_token)
    if gps_access_token:
        background_tasks.add_task(cerrar_sesion_supabase, gps_access_token)
    response.delete_cookie("gps_access_token", path="/")
    response.delete_cookie("gps_refresh_token", path="/auth")
    return {"estado": "sesion_cerrada"}
