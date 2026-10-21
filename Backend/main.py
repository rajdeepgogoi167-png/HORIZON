import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv()

from app.database import Base, SessionLocal, engine
from app.routers import (
    auth,
    blood,
    catalog,
    consultations,
    doctors,
    hospitals,
    network,
    patients,
    records,
    services,
    signaling,
)
from app.seed import seed_if_empty

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "Frontend"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Horizon Telemedicine API",
    description="Integrated Horizon care platform: adaptive consultations, compressed records, referrals, and blood requests.",
    version="2.1.0",
    lifespan=lifespan,
)

raw_origins = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
allow_all = not origins or origins == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else origins,
    allow_origin_regex=None if allow_all else r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)

app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(consultations.router)
app.include_router(network.router)
app.include_router(records.router)
app.include_router(signaling.router)
app.include_router(catalog.router)
app.include_router(hospitals.router)
app.include_router(blood.router)
app.include_router(services.router)


@app.get("/health")
def health():
    return {"ok": True, "service": "horizon"}


@app.get("/api")
def api_root():
    return {
        "message": "Horizon telemedicine backend",
        "docs": "/docs",
        "app": "/",
        "features": [
            "role-based sessions",
            "adaptive video/audio/chat modes",
            "compressed medical uploads",
            "store-and-forward messaging",
            "WebRTC signaling with HTTP fallback",
            "referrals and blood requests",
        ],
    }


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
