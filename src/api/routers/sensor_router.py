"""
Router para endpoints de sensores.

Proporciona acceso a las lecturas en tiempo real de los sensores
y gestión de configuración de sensores en las líneas de alimentación.
"""


from fastapi import APIRouter, HTTPException, status

from api.dependencies import (
    GetLineSensorsUseCaseDep,
    GetSensorReadingsUseCaseDep,
    UpdateSensorUseCaseDep,
)
from api.models.sensors import (
    SensorDetailResponse,
    SensorReadingResponse,
    SensorReadingsResponse,
    SensorsListResponse,
    UpdateSensorRequest,
)
from application.dtos.sensor_dtos import UpdateSensorDTO
from application.use_cases.sensors import SensorNotFoundException
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


@router.get(
    "/{line_id}/sensors",
    response_model=SensorsListResponse,
    summary="Listar sensores de una línea",
    description="""
    Obtiene la lista de sensores configurados en una línea de alimentación.

    Retorna información de cada sensor incluyendo:
    - ID y nombre del sensor
    - Tipo de sensor (Temperatura, Presión, Caudal)
    - Estado habilitado/deshabilitado
    - Umbrales de warning y critical configurados
    """,
    responses={
        200: {"description": "Lista de sensores obtenida exitosamente"},
        404: {"description": "Línea de alimentación no encontrada"},
    },
)
async def list_sensors(
    line_id: str,
    use_case: GetLineSensorsUseCaseDep,
) -> SensorsListResponse:
    """Lista todos los sensores de una línea."""
    try:
        result = await use_case.execute(line_id)

        return SensorsListResponse(
            line_id=result.line_id,
            sensors=[
                SensorDetailResponse(
                    id=s.id,
                    name=s.name,
                    sensor_type=s.sensor_type,
                    is_enabled=s.is_enabled,
                    warning_threshold=s.warning_threshold,
                    critical_threshold=s.critical_threshold,
                )
                for s in result.sensors
            ],
        )
    except FeedingLineNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{line_id}/sensors/{sensor_id}",
    response_model=SensorDetailResponse,
    summary="Actualizar configuración de un sensor",
    description="""
    Actualiza la configuración de un sensor específico.

    Campos actualizables:
    - **name**: Nuevo nombre del sensor
    - **is_enabled**: Habilitar/deshabilitar el sensor
    - **warning_threshold**: Umbral de advertencia (enviar null para limpiar)
    - **critical_threshold**: Umbral crítico (enviar null para limpiar)

    Los sensores deshabilitados no se incluyen en las lecturas de `/sensors/readings`.
    """,
    responses={
        200: {"description": "Sensor actualizado exitosamente"},
        404: {"description": "Línea o sensor no encontrado"},
    },
)
async def update_sensor(
    line_id: str,
    sensor_id: str,
    request: UpdateSensorRequest,
    use_case: UpdateSensorUseCaseDep,
) -> SensorDetailResponse:
    """Actualiza la configuración de un sensor."""
    try:
        # Convertir request a DTO
        update_dto = UpdateSensorDTO(
            name=request.name,
            is_enabled=request.is_enabled,
            warning_threshold=request.warning_threshold,
            critical_threshold=request.critical_threshold,
        )

        result = await use_case.execute(line_id, sensor_id, update_dto)

        return SensorDetailResponse(
            id=result.id,
            name=result.name,
            sensor_type=result.sensor_type,
            is_enabled=result.is_enabled,
            warning_threshold=result.warning_threshold,
            critical_threshold=result.critical_threshold,
        )
    except FeedingLineNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SensorNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
