# GPS Fútbol

Aplicación FastAPI para capturar lotes GPS desde un teléfono móvil y analizar
seis variables físicas de jugadores juveniles amateur de 14 a 18 años:
distancia total, velocidad máxima, HSR, sprints, deceleraciones y distancia por
minuto.

## Tecnologías

- FastAPI y Uvicorn
- Supabase PostgreSQL mediante API REST
- HTML, CSS y JavaScript
- Leaflet, leaflet.heat y Chart.js

## Ejecución local

1. Crea y activa un entorno virtual.
2. Instala las dependencias:

```powershell
cd backend
pip install -r requirements.txt
```

3. Crea `backend/.env` tomando como referencia `.env.example`.
4. Ejecuta las pruebas:

```powershell
python -m unittest discover -s tests -v
```

5. Ejecuta:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Abre:

- Aplicación: `http://127.0.0.1:8000/dashboard`
- Captura móvil: `http://127.0.0.1:8000/app`
- API: `http://127.0.0.1:8000/docs`
- Estado: `http://127.0.0.1:8000/health/`

## Variables de entorno

```env
SUPABASE_URL=
SUPABASE_ANON_KEY=
ENVIRONMENT=development
CORS_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
DOCS_ENABLED=true
```

En producción, `CORS_ORIGINS` debe contener la URL HTTPS pública del servicio.
Las claves de Supabase deben configurarse como secretos del proveedor y nunca
subirse al repositorio.

## Flujo

1. El coach selecciona o crea su perfil.
2. Registra un jugador y crea una sesión.
3. Selecciona jugador y sesión.
4. El teléfono abre `/app`, captura puntos localmente y envía el lote a
   `POST /gps/lote`.
5. El backend guarda los puntos, calcula las seis métricas y las almacena.
6. El dashboard muestra métricas, cancha, recorrido, heatmap e historial.
7. Reportes permite generar el resumen y guardarlo como PDF mediante la opción
   de impresión del navegador.

## Despliegue en Render

El repositorio incluye `render.yaml`.

1. Sube el proyecto a un repositorio privado de GitHub.
2. En Render crea un Blueprint o Web Service desde ese repositorio.
3. Ejecuta `supabase/00_reparar_columnas.sql` en una consulta nueva.
4. Comprueba que ambas columnas devuelvan el valor `1`.
5. Ejecuta `supabase/rls_policies.sql` en otra consulta nueva.
6. Ejecuta `supabase/02_proteger_tablas_auxiliares.sql`.
7. Configura `SUPABASE_URL`, `SUPABASE_ANON_KEY` y `CORS_ORIGINS`.
8. Usa `/health/` como health check.
9. Render ejecutará:

```text
pip install -r requirements.txt && python -m unittest discover -s tests -v
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Después del primer despliegue, configura en Supabase:

- **Site URL:** `https://TU-SERVICIO.onrender.com`
- **Redirect URL:** `https://TU-SERVICIO.onrender.com/auth/callback`

## Prueba móvil con ngrok

Con FastAPI ejecutándose:

```powershell
ngrok http 8000
```

Abre en el teléfono la URL HTTPS generada, seguida de `/app`.

## Endpoints principales

- `GET /coaches/`, `POST /coaches/`, `DELETE /coaches/{id}`
- `GET /jugadores/`, `POST /jugadores/`, `DELETE /jugadores/{id}`
- `GET /sesiones/`, `POST /sesiones/`, `PATCH /sesiones/{id}/estado`
- `POST /gps/lote`, `GET /gps/sesion/{sesion_id}`
- `GET /metricas/perfil`, `GET /metricas/guardadas/{sesion_id}`
- `GET /historial/jugador/{jugador_id}`
- `GET /reportes/sesion/{sesion_id}`
- `GET /demo/sesion`

## Autenticación y seguridad

- Registro e inicio de sesión mediante Supabase Auth.
- Tokens almacenados en cookies `HttpOnly`; no quedan expuestos a JavaScript.
- FastAPI valida el JWT antes de atender endpoints privados.
- El backend asigna jugadores y sesiones al coach autenticado.
- Las políticas RLS aíslan coaches, jugadores, sesiones, GPS y métricas.
- El teléfono reutiliza la sesión autenticada del mismo navegador y origen.

En `Supabase > Authentication > URL Configuration`, agrega como Redirect URLs:

```text
http://127.0.0.1:8000/auth/callback
http://localhost:8000/auth/callback
https://TU-DOMINIO/auth/callback
```

Para registro directo sin verificación de correo, desactiva **Confirm email** en
`Authentication > Providers > Email`. En ese modo, el registro devuelve una
sesión inmediatamente y la aplicación abre el dashboard sin enviar correos.

No uses una clave `service_role` como `SUPABASE_ANON_KEY`. La aplicación debe
usar la clave pública `anon` o `publishable`; la autorización efectiva depende
del JWT del usuario y de las políticas RLS.

### Datos creados antes de activar autenticación

Las filas antiguas de `coaches` deben asociarse manualmente con el UUID de
`Authentication > Users`. Los jugadores antiguos también necesitan su
`coach_id`. El archivo SQL incluye un ejemplo al final. Haz esta asociación
antes de usar la aplicación, porque RLS ocultará las filas sin propietario.

Para datos reales de menores también deben definirse consentimiento, retención,
eliminación y acceso institucional conforme a la normativa aplicable.
