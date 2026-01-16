# Lectura de Sensores en Tiempo Real

## Resumen

El sistema ahora soporta la lectura en tiempo real de sensores asociados a las líneas de alimentación. Los valores de los sensores varían dinámicamente según el estado operativo de la máquina (en reposo vs alimentando).

## Tipos de Sensores

Cada línea de alimentación puede tener hasta **3 sensores** (uno de cada tipo):

| Tipo | Descripción | Unidad | Valores Esperados |
|------|-------------|--------|-------------------|
| **TEMPERATURE** | Temperatura del aire | °C | Reposo: ~15°C, Alimentando: ~25°C |
| **PRESSURE** | Presión del aire | bar | Reposo: ~0.2 bar, Alimentando: ~0.8 bar |
| **FLOW** | Flujo de aire | m³/min | Reposo: ~0 m³/min, Alimentando: ~15 m³/min |

## Umbrales de Alerta

El sistema detecta automáticamente condiciones de advertencia y críticas:

| Sensor | Warning | Critical |
|--------|---------|----------|
| Temperature | > 70°C | > 85°C |
| Pressure | > 1.3 bar | > 1.5 bar |
| Flow | > 18 m³/min | > 22 m³/min |

## API Endpoint

### GET `/api/feeding-lines/{line_id}/sensors/readings`

Obtiene las lecturas en tiempo real de todos los sensores de una línea de alimentación.

#### Parámetros

- `line_id` (path, required): UUID de la línea de alimentación

#### Respuesta Exitosa (200)

```json
{
  "line_id": "6e0e6354-6961-4853-a052-8e1150afe5b6",
  "timestamp": "2026-01-15T11:25:52.656005",
  "readings": [
    {
      "sensor_id": "6e0e6354-6961-4853-a052-8e1150afe5b6-temp",
      "sensor_type": "Temperatura",
      "value": 24.5,
      "unit": "°C",
      "timestamp": "2026-01-15T11:25:52.656005",
      "is_warning": false,
      "is_critical": false
    },
    {
      "sensor_id": "6e0e6354-6961-4853-a052-8e1150afe5b6-pressure",
      "sensor_type": "Presión",
      "value": 0.78,
      "unit": "bar",
      "timestamp": "2026-01-15T11:25:52.656005",
      "is_warning": false,
      "is_critical": false
    },
    {
      "sensor_id": "6e0e6354-6961-4853-a052-8e1150afe5b6-flow",
      "sensor_type": "Caudal",
      "value": 14.8,
      "unit": "m³/min",
      "timestamp": "2026-01-15T11:25:52.656005",
      "is_warning": false,
      "is_critical": false
    }
  ]
}
```

#### Errores

- **404**: Línea de alimentación no encontrada
- **500**: Error interno del servidor

## Ejemplo de Uso

### cURL

```bash
# Obtener lecturas de sensores de una línea
curl -X GET "http://localhost:8000/api/feeding-lines/{line_id}/sensors/readings"
```

### Python

```python
import requests

line_id = "6e0e6354-6961-4853-a052-8e1150afe5b6"
response = requests.get(f"http://localhost:8000/api/feeding-lines/{line_id}/sensors/readings")

if response.status_code == 200:
    data = response.json()
    for reading in data["readings"]:
        status = ""
        if reading["is_critical"]:
            status = "⚠️ CRITICAL"
        elif reading["is_warning"]:
            status = "⚠️ WARNING"
        
        print(f"{reading['sensor_type']}: {reading['value']} {reading['unit']} {status}")
```

### JavaScript (Frontend)

```javascript
async function getSensorReadings(lineId) {
  const response = await fetch(`/api/feeding-lines/${lineId}/sensors/readings`);
  const data = await response.json();
  
  return data.readings.map(reading => ({
    type: reading.sensor_type,
    value: reading.value,
    unit: reading.unit,
    hasWarning: reading.is_warning,
    hasCritical: reading.is_critical,
    timestamp: new Date(reading.timestamp)
  }));
}

// Polling cada 2 segundos
setInterval(async () => {
  const readings = await getSensorReadings(lineId);
  updateDashboard(readings);
}, 2000);
```

## Arquitectura

### Capas Implementadas

```
┌─────────────────────────────────────────┐
│  API Layer                              │
│  GET /api/feeding-lines/{id}/sensors/  │
│  readings                               │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Application Layer                      │
│  GetSensorReadingsUseCase               │
│  - Valida que la línea existe           │
│  - Solicita lecturas al PLC             │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Domain Layer                           │
│  IFeedingMachine.get_sensor_readings()  │
│  - Interfaz para lectura de sensores    │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Infrastructure Layer                   │
│  PLCSimulator / PLCModbusClient         │
│  - Simulación: valores dinámicos        │
│  - Real: lectura vía Modbus             │
└─────────────────────────────────────────┘
```

### DTOs

**SensorReading**: Representa una lectura individual
```python
@dataclass(frozen=True)
class SensorReading:
    sensor_id: str
    sensor_type: SensorType
    value: float
    unit: str
    timestamp: datetime
    is_warning: bool = False
    is_critical: bool = False
```

**SensorReadings**: Colección de lecturas de una línea
```python
@dataclass(frozen=True)
class SensorReadings:
    line_id: str
    readings: List[SensorReading]
    timestamp: datetime
```

## Implementación Actual

### Modo Simulación (Desarrollo)

Los valores se generan dinámicamente en `PLCSimulator`:

- **En reposo** (máquina no running):
  - Temperatura: 15°C ± 2°C
  - Presión: 0.2 bar ± 0.05 bar
  - Flujo: 0 m³/min (+ ruido mínimo)

- **Durante alimentación** (máquina running):
  - Temperatura: 25°C ± 2°C
  - Presión: 0.8 bar ± 0.05 bar
  - Flujo: 15 m³/min ± 1.5 m³/min

### Modo Producción (PLC Real)

Para integrar con PLC real vía Modbus, ver documentación en:
- `docs/INTEGRACION_PLC.md`

Registros Modbus sugeridos para sensores:

| Parámetro | Tipo | Descripción | Ejemplo Modbus |
|-----------|------|-------------|----------------|
| TEMPERATURE_SENSOR_VALUE | float | Temperatura del aire (°C) | Registros 3000-3001 |
| PRESSURE_SENSOR_VALUE | float | Presión del aire (bar) | Registros 3002-3003 |
| FLOW_SENSOR_VALUE | float | Flujo de aire (m³/min) | Registros 3004-3005 |

## Casos de Uso

### Dashboard de Alimentación

El endpoint está diseñado para polling frecuente desde el dashboard:

```javascript
// Actualizar cada 2 segundos
const POLL_INTERVAL = 2000;

function startSensorMonitoring(lineId) {
  return setInterval(async () => {
    try {
      const response = await fetch(
        `/api/feeding-lines/${lineId}/sensors/readings`
      );
      const data = await response.json();
      
      // Actualizar UI
      updateTemperatureGauge(data.readings[0]);
      updatePressureGauge(data.readings[1]);
      updateFlowGauge(data.readings[2]);
      
      // Verificar alertas
      checkAlerts(data.readings);
    } catch (error) {
      console.error('Error reading sensors:', error);
    }
  }, POLL_INTERVAL);
}
```

### Monitoreo de Alertas

```javascript
function checkAlerts(readings) {
  readings.forEach(reading => {
    if (reading.is_critical) {
      showCriticalAlert(reading);
      notifyOperator(reading);
    } else if (reading.is_warning) {
      showWarning(reading);
    }
  });
}
```

### Registro Histórico (Futuro)

Actualmente, las lecturas son en tiempo real sin almacenamiento histórico. Para implementar historial:

1. Crear tabla `sensor_readings_log`
2. Agregar background task para guardar lecturas periódicamente
3. Crear endpoint `GET /api/sensors/history`

## Testing

### Test Manual

```bash
# 1. Obtener ID de una línea
curl http://localhost:8000/api/feeding-lines | jq '.feeding_lines[0].id'

# 2. Leer sensores
LINE_ID="6e0e6354-6961-4853-a052-8e1150afe5b6"
curl "http://localhost:8000/api/feeding-lines/$LINE_ID/sensors/readings" | jq
```

### Test Automatizado

Ver: `test_sensor_endpoint.py`

```bash
PYTHONPATH=src python test_sensor_endpoint.py
```

## Próximos Pasos

1. **Almacenamiento Histórico**: Guardar lecturas en base de datos
2. **WebSocket/SSE**: Streaming en tiempo real en lugar de polling
3. **Gráficas**: Endpoints para datos históricos con agregaciones
4. **Calibración**: Endpoints para calibrar sensores
5. **Alertas Configurables**: Umbrales personalizables por línea
6. **Integración PLC Real**: Implementar `PLCModbusClient.get_sensor_readings()`

## Documentación Relacionada

- [Integración con PLC](./INTEGRACION_PLC.md)
- [API Cages](./API_CAGES.md)
- [CLAUDE.md](../CLAUDE.md)
