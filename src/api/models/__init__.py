"""
Modelos de API (Pydantic) para validación de requests/responses de FastAPI.

Estos modelos son la capa de presentación y se mapean a los DTOs de aplicación.
Organizados por dominio para escalabilidad.
"""

from .system_layout import (
    # Request/Response principales
    SystemLayoutModel,
    
    # Agregados independientes
    SiloConfigModel,
    CageConfigModel,
    
    # Agregado dependiente
    FeedingLineConfigModel,
    
    # Componentes
    BlowerConfigModel,
    SensorConfigModel,
    DoserConfigModel,
    SelectorConfigModel,
    
    # Value Objects
    SlotAssignmentModel,
    
    # Presentation
    PresentationDataModel,
)

__all__ = [
    # Request/Response
    'SystemLayoutModel',
    
    # Agregados
    'SiloConfigModel',
    'CageConfigModel',
    'FeedingLineConfigModel',
    
    # Componentes
    'BlowerConfigModel',
    'SensorConfigModel',
    'DoserConfigModel',
    'SelectorConfigModel',
    
    # Value Objects
    'SlotAssignmentModel',
    
    # Presentation
    'PresentationDataModel',
]
