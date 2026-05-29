from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.routes import metricas

from app.routes import coaches
from app.routes import gps
from app.routes import reportes
from app.routes import historial

app = FastAPI(
    title="GPS Football Performance API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    coaches.router,
    prefix="/coaches",
    tags=["Coaches"]
)

app.include_router(
    gps.router,
    prefix="/gps",
    tags=["GPS"]
)

@app.get("/")
def home():

    return {
        "message":"API funcionando"
    }
    
@app.get("/app")
def mobile_app():
    return FileResponse("app/index.html")

@app.get("/dashboard")
def dashboard():
    return FileResponse("app/dashboard.html")

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