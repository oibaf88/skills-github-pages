"""Punto de entrada de la aplicación FastAPI."""
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import Base, engine
from .routers import pages, api

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea las tablas si no existen (suficiente para portafolio; usar Alembic en producción).
    Base.metadata.create_all(bind=engine)
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="Portafolio fullstack en Python con FastAPI + Jinja2 + SQLite.",
    version="1.0.0",
    lifespan=lifespan,
)

# Archivos estáticos (imágenes, css adicional, favicon...)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Rutas HTML
app.include_router(pages.router)
# API REST con Swagger en /docs
app.include_router(api.router)
