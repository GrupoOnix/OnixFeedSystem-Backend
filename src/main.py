import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))


def configure_app_logging() -> None:
    """Configure application logs without overriding Uvicorn/FastAPI logging."""
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )

    for logger_name in ("api", "application", "domain", "infrastructure"):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.propagate = False


configure_app_logging()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import api_router
from infrastructure.services.background_tasks import lifespan_with_scheduler

app = FastAPI(
    title="Feeding System API",
    version="1.0.0",
    lifespan=lifespan_with_scheduler,
)

# CORS - TODO: Restringir origins en producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
