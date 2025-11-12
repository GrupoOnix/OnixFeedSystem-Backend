from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

# Agregar src al path para imports
sys.path.insert(0, str(Path(__file__).parent))

from api.routers import api_router

# ============================================================================
# Configuración de la aplicación FastAPI
# ============================================================================

app = FastAPI(
    title="Feeding System API",
    description="""
    API REST para el sistema de alimentación automatizado en acuicultura.
    
    ## Funcionalidades principales:
    
    * **System Layout**: Sincronización del layout completo del sistema (UC-01)
    * **Feeding Lines**: Gestión de líneas de alimentación
    * **Silos**: Gestión de silos de almacenamiento
    * **Cages**: Gestión de jaulas de cultivo
    
    ## Arquitectura:
    
    - **DDD (Domain-Driven Design)**: Lógica de negocio en el dominio
    - **Clean Architecture**: Separación de capas (API, Application, Domain, Infrastructure)
    - **CQRS**: Separación de comandos y consultas (futuro)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ============================================================================
# Configuración de CORS (para desarrollo)
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restringir en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Registro de routers
# ============================================================================

app.include_router(api_router)

# ============================================================================
# Health check endpoint
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Endpoint raíz - Health check."""
    return {
        "status": "ok",
        "message": "Feeding System API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint para monitoreo."""
    return {
        "status": "healthy",
        "service": "feeding-system-api"
    }

