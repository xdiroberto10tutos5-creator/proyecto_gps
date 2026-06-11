from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.config import CORS_ORIGINS, DOCS_ENABLED, ENVIRONMENT
from app.routes import auth
from app.routes import coaches
from app.routes import demo
from app.routes import gps
from app.routes import health as health_routes
from app.routes import historial
from app.routes import jugadores
from app.routes import metricas
from app.routes import reportes
from app.routes import sesiones
from app.security_context import reset_security_context, set_security_context
from app.services.auth_service import validar_token

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="GPS Football Performance API",
    version="1.0.0",
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )


@app.middleware("http")
async def security_headers(request, call_next):
    public_paths = {"/", "/app", "/dashboard", "/openapi.json", "/docs", "/redoc"}
    public_prefixes = (
        "/auth/login",
        "/auth/signup",
        "/auth/logout",
        "/auth/refresh",
        "/auth/resend",
        "/auth/status",
        "/auth/callback",
        "/auth/complete",
        "/demo/",
        "/health/",
    )
    path = request.url.path
    context_tokens = None

    if (
        request.method != "OPTIONS"
        and path not in public_paths
        and not path.startswith(public_prefixes)
    ):
        authorization = request.headers.get("Authorization", "")
        access_token = (
            authorization.removeprefix("Bearer ").strip()
            if authorization.startswith("Bearer ")
            else request.cookies.get("gps_access_token")
        )
        if not access_token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Se requiere una sesión autenticada"}
            )

        try:
            user = validar_token(access_token)
        except Exception as error:
            detail = getattr(error, "detail", "Sesión inválida o vencida")
            status_code = getattr(error, "status_code", 401)
            return JSONResponse(status_code=status_code, content={"detail": detail})

        context_tokens = set_security_context(access_token, user)

    try:
        response = await call_next(request)
    finally:
        if context_tokens:
            reset_security_context(context_tokens)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
    if ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Autenticación"]
)

app.include_router(
    coaches.router,
    prefix="/coaches",
    tags=["Coaches"]
)

app.include_router(
    demo.router,
    prefix="/demo",
    tags=["Demo"]
)

app.include_router(
    gps.router,
    prefix="/gps",
    tags=["GPS"]
)

app.include_router(
    sesiones.router,
    prefix="/sesiones",
    tags=["Sesiones"]
)


app.include_router(
    jugadores.router,
    prefix="/jugadores",
    tags=["Jugadores"]
)


@app.get("/")
def coach_app():

    return FileResponse(BASE_DIR / "dashboard.html")

@app.get("/app")
def mobile_app():
    return FileResponse(BASE_DIR / "index.html")

@app.get("/dashboard")
def dashboard():
    return FileResponse(BASE_DIR / "dashboard.html")

app.include_router(
    metricas.router,
    prefix="/metricas",
    tags=["Metricas"]
)

app.include_router(
    reportes.router,
    prefix="/reportes",
    tags=["Reportes"]
)

app.include_router(
    historial.router,
    prefix="/historial",
    tags=["Historial"]
)

app.include_router(
    health_routes.router,
    prefix="/health",
    tags=["Health"]
)
