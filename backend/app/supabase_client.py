import requests
from app.config import SUPABASE_URL, SUPABASE_KEY

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def insert_data(table, data):

    url = f"{SUPABASE_URL}/rest/v1/{table}"

    response = requests.post(
        url,
        headers=HEADERS,
        json=data
    )

    response.raise_for_status()

    return response.json()


def update_data(table, data, column, value):

    url = f"{SUPABASE_URL}/rest/v1/{table}?{column}=eq.{value}"

    response = requests.patch(
        url,
        headers=HEADERS,
        json=data
    )

    response.raise_for_status()

    return response.json()


def get_data(table, column, value):

    url = f"{SUPABASE_URL}/rest/v1/{table}?{column}=eq.{value}"

    response = requests.get(
        url,
        headers=HEADERS
    )

    response.raise_for_status()

    return response.json()


def get_gps_by_sesion(sesion_id):

    url = f"{SUPABASE_URL}/rest/v1/gps_data?sesion_id=eq.{sesion_id}&order=timestamp.asc"

    response = requests.get(
        url,
        headers=HEADERS
    )

    response.raise_for_status()

    return response.json()


def insert_metricas(data):

    url = f"{SUPABASE_URL}/rest/v1/metricas"

    response = requests.post(
        url,
        headers=HEADERS,
        json=data
    )

    response.raise_for_status()

    return response.json()

def get_metricas_by_sesion(sesion_id):
    url = f"{SUPABASE_URL}/rest/v1/metricas?sesion_id=eq.{sesion_id}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_metricas_by_jugador(jugador_id):
    url = f"{SUPABASE_URL}/rest/v1/metricas?jugador_id=eq.{jugador_id}&order=id.asc"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()