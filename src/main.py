import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import api_router
from infrastructure.services.background_tasks import lifespan_with_scheduler

app = FastAPI(
    title="Feeding System API",
    version="1.0.0",
    lifespan=lifespan_with_scheduler,
)

# CORS - lee origins desde variable de entorno (comma-separated)
_cors_origins_raw = os.getenv("CORS_ORIGINS", "")
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()] if _cors_origins_raw else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "version": "1.0.0",
        "message": "Feeding System API is running",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
