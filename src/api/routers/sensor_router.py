"""
Router para endpoints de sensores.

Proporciona acceso a las lecturas en tiempo real de los sensores
asociados a las líneas de alimentación.
"""

from fastapi import APIRouter, HTTPException, status

from api.dependencies import GetSensorReadingsUseCaseDep
from api.models.sensors import SensorReadingResponse, SensorReadingsResponse
from domain.exceptions import FeedingLineNotFoundException

router = APIRouter(prefix="/feeding-lines", tags=["sensors"])


@router.get(
    "/{line_id}/sensors/readings",
    response_model=SensorReadingsResponse,
    summary="Obtener lecturas de sensores de una línea",
    description="""
    Obtiene las lecturas en tiempo real de todos los sensores asociados a una línea de alimentación.

    Los sensores pueden ser de 3 tipos:
    - **TEMPERATURE**: Temperatura del aire en °C
    - **PRESSURE**: Presión del aire en bar
    - **FLOW**: Flujo de aire en m³/min

    Los valores varían según el estado de la máquina:
    - **En reposo**: Temperatura ~15°C, Presión ~0.2 bar, Flujo ~0 m³/min
    - **Durante alimentación**: Temperatura ~25°C, Presión ~0.8 bar, Flujo ~15 m³/min

    Cada lectura incluye flags de advertencia (warning) y crítico (critical) basados en umbrales predefinidos.

    **Notas de implementación**:
    - Los datos se obtienen por polling (consulta bajo demanda)
    - En producción, los valores provienen del PLC vía Modbus
    - En desarrollo, se simulan valores realistas
    """,
    responses={
        200: {
            "description": "Lecturas de sensores obtenidas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "line_id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2025-01-15T10:30:00.000Z",
                        "readings": [
                            {
                                "sensor_id": "550e8400-e29b-41d4-a716-446655440000-temp",
                                "sensor_type": "TEMPERATURE",
                                "value": 24.5,
                                "unit": "°C",
                                "timestamp": "2025-01-15T10:30:00.000Z",
                                "is_warning": False,
                                "is_critical": False,
                            },
                            {
                                "sensor_id": "550e8400-e29b-41d4-a716-446655440000-pressure",
                                "sensor_type": "PRESSURE",
                                "value": 0.78,
                                "unit": "bar",
                                "timestamp": "2025-01-15T10:30:00.000Z",
                                "is_warning": False,
                                "is_critical": False,
                            },
                            {
                                "sensor_id": "550e8400-e29b-41d4-a716-446655440000-flow",
                                "sensor_type": "FLOW",
                                "value": 14.8,
                                "unit": "m³/min",
                                "timestamp": "2025-01-15T10:30:00.000Z",
                                "is_warning": False,
                                "is_critical": False,
                            },
                        ],
                    }
                }
            },
        },
        404: {"description": "Línea de alimentación no encontrada"},
    },
)
async def get_sensor_readings(
    line_id: str,
    use_case: GetSensorReadingsUseCaseDep,
) -> SensorReadingsResponse:
    """
    Endpoint para obtener lecturas en tiempo real de sensores de una línea.

    Este endpoint está diseñado para ser consultado periódicamente desde el dashboard
    de alimentación para mostrar el estado actual de los sensores.
    """
    try:
        # Ejecutar caso de uso
        sensor_readings = await use_case.execute(line_id)

        # Convertir a modelo de respuesta
        return SensorReadingsResponse(
            line_id=sensor_readings.line_id,
            readings=[
                SensorReadingResponse(
                    sensor_id=reading.sensor_id,
                    sensor_type=reading.sensor_type.value,
                    value=reading.value,
                    unit=reading.unit,
                    timestamp=reading.timestamp,
                    is_warning=reading.is_warning,
                    is_critical=reading.is_critical,
                )
                for reading in sensor_readings.readings
            ],
            timestamp=sensor_readings.timestamp,
        )

    except FeedingLineNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener lecturas de sensores: {str(e)}",
        )
