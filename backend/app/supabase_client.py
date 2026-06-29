import requests
from urllib.parse import quote
from fastapi import HTTPException
from app.config import SUPABASE_ANON_KEY, SUPABASE_URL
from app.security_context import get_access_token

TIMEOUT = 15

def request_supabase(method, path, **kwargs):
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=500,
            detail="Faltan SUPABASE_URL o SUPABASE_ANON_KEY"
        )

    url = f"{SUPABASE_URL}/rest/v1/{path}"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    access_token = get_access_token()
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    try:
        response = requests.request(
            method,
            url,
            headers=headers,
            timeout=TIMEOUT,
            **kwargs
        )
        response.raise_for_status()
    except requests.HTTPError as error:
        detail = response.text
        try:
            detail = response.json()
        except ValueError:
            pass

        raise HTTPException(
            status_code=response.status_code,
            detail=detail
        ) from error
    except requests.RequestException as error:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo conectar con Supabase: {error}"
        ) from error

    if response.content:
        return response.json()

    return []


def list_data(table, order="id.asc"):
    return request_supabase("get", f"{table}?order={order}")


def insert_data(table, data):

    return request_supabase("post", table, json=data)


def update_data(table, data, column, value):

    return request_supabase(
        "patch",
        f"{table}?{column}=eq.{quote(str(value))}",
        json=data
    )


def get_data(table, column, value):

    return request_supabase("get", f"{table}?{column}=eq.{quote(str(value))}")


def delete_data(table, column, value):
    return request_supabase(
        "delete",
        f"{table}?{column}=eq.{quote(str(value))}"
    )


def delete_metricas_by_sesion_jugador(sesion_id, jugador_id):
    return request_supabase(
        "delete",
        (
            f"metricas?sesion_id=eq.{quote(str(sesion_id))}"
            f"&jugador_id=eq.{quote(str(jugador_id))}"
        )
    )


def delete_metricas_by_sesion(sesion_id):
    return request_supabase(
        "delete",
        f"metricas?sesion_id=eq.{quote(str(sesion_id))}"
    )


def delete_gps_by_sesion_jugador(sesion_id, jugador_id):
    return request_supabase(
        "delete",
        (
            f"gps_data?sesion_id=eq.{quote(str(sesion_id))}"
            f"&jugador_id=eq.{quote(str(jugador_id))}"
        )
    )


def delete_gps_by_sesion(sesion_id):
    return request_supabase(
        "delete",
        f"gps_data?sesion_id=eq.{quote(str(sesion_id))}"
    )


def get_gps_by_sesion(sesion_id):

    url = (
        f"{SUPABASE_URL}/rest/v1/gps_data"
        f"?sesion_id=eq.{quote(str(sesion_id))}"
        f"&order=timestamp.asc"
    )

    return request_supabase("get", url.replace(f"{SUPABASE_URL}/rest/v1/", ""))


def get_gps_by_sesion_jugador(sesion_id, jugador_id):

    url = (
        f"{SUPABASE_URL}/rest/v1/gps_data"
        f"?sesion_id=eq.{quote(str(sesion_id))}"
        f"&jugador_id=eq.{quote(str(jugador_id))}"
        f"&order=timestamp.asc"
    )

    return request_supabase("get", url.replace(f"{SUPABASE_URL}/rest/v1/", ""))


def insert_metricas(data):

    return insert_data("metricas", data)

def get_metricas_by_sesion(sesion_id):
    return request_supabase(
        "get",
        f"metricas?sesion_id=eq.{quote(str(sesion_id))}&order=id.asc"
    )

def get_metricas_by_sesion_jugador(sesion_id, jugador_id):
    return request_supabase(
        "get",
        (
            f"metricas?sesion_id=eq.{quote(str(sesion_id))}"
            f"&jugador_id=eq.{quote(str(jugador_id))}"
            f"&order=id.asc"
        )
    )

def get_metricas_by_jugador(jugador_id):
    return request_supabase(
        "get",
        f"metricas?jugador_id=eq.{quote(str(jugador_id))}&order=id.asc"
    )
