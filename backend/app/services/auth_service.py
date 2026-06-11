import threading
import time

import requests
from urllib.parse import quote
from fastapi import HTTPException

from app.config import SUPABASE_ANON_KEY, SUPABASE_URL
from app.security_context import get_auth_user
from app.supabase_client import get_data, insert_data

AUTH_TIMEOUT = 15
TOKEN_CACHE_TTL = 45
_token_cache = {}
_token_cache_lock = threading.Lock()


def _auth_request(method, path, access_token=None, **kwargs):
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=500,
            detail="Faltan SUPABASE_URL o SUPABASE_ANON_KEY"
        )

    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    try:
        response = requests.request(
            method,
            f"{SUPABASE_URL}/auth/v1/{path}",
            headers=headers,
            timeout=AUTH_TIMEOUT,
            **kwargs,
        )
    except requests.RequestException as error:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo conectar con Supabase Auth: {error}"
        ) from error

    if not response.ok:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        error_code = detail.get("error_code") if isinstance(detail, dict) else None
        mensajes = {
            "invalid_credentials": "Correo o contraseña incorrectos.",
            "email_not_confirmed": "Confirma tu correo electrónico antes de iniciar sesión.",
            "user_already_exists": "Ya existe una cuenta con este correo.",
            "email_exists": "Ya existe una cuenta con este correo.",
            "over_email_send_rate_limit": (
                "Supabase alcanzó el límite temporal de correos. "
                "Eliminar usuarios no reinicia el límite; espera hasta una hora "
                "o crea un usuario confirmado desde el panel de Supabase."
            ),
            "weak_password": "La contraseña no cumple los requisitos de seguridad.",
        }
        raise HTTPException(
            status_code=response.status_code,
            detail=mensajes.get(error_code, detail)
        )

    return response.json() if response.content else {}


def registrar_coach(nombre, email, password, redirect_to=None):
    path = "signup"
    if redirect_to:
        path = f"signup?redirect_to={quote(redirect_to, safe=':/')}"
    return _auth_request(
        "post",
        path,
        json={
            "email": email,
            "password": password,
            "data": {"nombre": nombre},
        },
    )


def iniciar_sesion(email, password):
    return _auth_request(
        "post",
        "token?grant_type=password",
        json={"email": email, "password": password},
    )


def renovar_sesion(refresh_token):
    return _auth_request(
        "post",
        "token?grant_type=refresh_token",
        json={"refresh_token": refresh_token},
    )


def validar_token(access_token):
    now = time.monotonic()
    with _token_cache_lock:
        cached = _token_cache.get(access_token)
        if cached and cached["expires_at"] > now:
            return cached["user"]
        if cached:
            _token_cache.pop(access_token, None)

    user = _auth_request("get", "user", access_token=access_token)
    guardar_token_cache(access_token, user)
    return user


def guardar_token_cache(access_token, user):
    now = time.monotonic()
    with _token_cache_lock:
        expired_tokens = [
            token
            for token, entry in _token_cache.items()
            if entry["expires_at"] <= now
        ]
        for token in expired_tokens:
            _token_cache.pop(token, None)
        _token_cache[access_token] = {
            "user": user,
            "expires_at": now + TOKEN_CACHE_TTL,
        }


def invalidar_token_cache(access_token):
    if not access_token:
        return
    with _token_cache_lock:
        _token_cache.pop(access_token, None)


def cerrar_sesion_supabase(access_token):
    return _auth_request("post", "logout", access_token=access_token)


def reenviar_confirmacion(email, redirect_to=None):
    payload = {
        "type": "signup",
        "email": email,
    }
    if redirect_to:
        payload["options"] = {"email_redirect_to": redirect_to}
    return _auth_request("post", "resend", json=payload)


def obtener_coach_actual():
    user = get_auth_user()
    coaches = get_data("coaches", "user_id", user["id"])
    if not coaches:
        metadata = user.get("user_metadata") or {}
        nombre = (
            metadata.get("nombre")
            or metadata.get("name")
            or str(user.get("email") or "Coach").split("@")[0]
        )
        creado = insert_data(
            "coaches",
            {
                "user_id": user["id"],
                "nombre": nombre,
                "email": user.get("email"),
            },
        )
        if not creado:
            raise HTTPException(
                status_code=403,
                detail="No se pudo crear el perfil del coach autenticado"
            )
        return creado[0]
    return coaches[0]


def obtener_estado_auth():
    settings = _auth_request("get", "settings")
    try:
        from app.supabase_client import request_supabase
        request_supabase("get", "coaches?select=id,user_id,email&limit=1")
        request_supabase("get", "jugadores?select=id,coach_id&limit=1")
        esquema_listo = True
        detalle = None
    except HTTPException as error:
        detail_text = str(error.detail).lower()
        # Después de activar RLS, anon debe recibir permission denied.
        esquema_listo = (
            error.status_code in {401, 403}
            and (
                "permission denied" in detail_text
                or "42501" in detail_text
            )
        )
        detalle = None if esquema_listo else error.detail

    return {
        "auth_habilitado": bool(settings.get("external", {}).get("email")),
        "registro_habilitado": not bool(settings.get("disable_signup")),
        "confirmacion_email_requerida": not bool(settings.get("mailer_autoconfirm")),
        "esquema_rls_listo": esquema_listo,
        "detalle_esquema": detalle,
    }
