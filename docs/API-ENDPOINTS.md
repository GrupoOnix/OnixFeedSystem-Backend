# API Endpoints - Feeding System Backend

> **Documentacion completa de todos los endpoints REST del sistema**
> 
> Base URL: `http://localhost:8000`
> Swagger UI: `http://localhost:8000/docs`

---

## Indice

1. [System](#1-system)
2. [System Layout](#2-system-layout)
3. [Feeding Operations](#3-feeding-operations)
4. [Feeding Lines](#4-feeding-lines)
5. [Device Control](#5-device-control)
6. [Sensors](#6-sensors)
7. [Cages](#7-cages)
8. [Cage Groups](#8-cage-groups)
9. [Silos](#9-silos)
10. [Foods](#10-foods)
11. [Alerts](#11-alerts)

---

## 1. System

Endpoints de estado del sistema.

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/system/status` | Estado del sistema |

### GET /system/status
Retorna el estado actual del sistema.

**Response:**
```json
{
  "status": "ok"
}
```

---

## 2. System Layout

Configuracion y sincronizacion del trazado del sistema.

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/system-layout` | Sincroniza el trazado del sistema |
| GET | `/system-layout/export` | Exporta la configuracion actual |

### POST /system-layout
Sincroniza la configuracion completa del sistema (lineas, jaulas, silos, asignaciones).

**Request Body:** `SystemLayoutModel`

### GET /system-layout/export
Exporta la configuracion actual del sistema en formato JSON.

---

## 3. Feeding Operations

Operaciones de alimentacion (iniciar, detener, pausar, reanudar).

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/feeding/start` | Inicia sesion de alimentacion |
| POST | `/feeding/lines/{line_id}/stop` | Detiene alimentacion activa |
| POST | `/feeding/lines/{line_id}/pause` | Pausa alimentacion |
| POST | `/feeding/lines/{line_id}/resume` | Reanuda alimentacion pausada |
| PATCH | `/feeding/lines/{line_id}/parameters` | Actualiza parametros en caliente |

### POST /feeding/start
Inicia una nueva sesion/operacion de alimentacion en una linea.

**Request Body:**
```json
{
  "line_id": "uuid",
  "cage_id": "uuid",
  "mode": "MANUAL",
  "target_amount_kg": 100.0,
  "blower_speed_percentage": 75.0,
  "dosing_rate_kg_min": 2.5
}
```

**Response (201):**
```json
{
  "session_id": "uuid",
  "message": "Feeding session started successfully"
}
```

### POST /feeding/lines/{line_id}/stop
Detiene la alimentacion activa en una linea.

**Response (200):**
```json
{
  "message": "Feeding session stopped successfully"
}
```

### POST /feeding/lines/{line_id}/pause
Pausa temporalmente la alimentacion.

### POST /feeding/lines/{line_id}/resume
Reanuda una alimentacion pausada.

### PATCH /feeding/lines/{line_id}/parameters
Actualiza parametros de alimentacion sin detener la operacion.

**Request Body:**
```json
{
  "blower_speed": 80.0,
  "dosing_rate": 3.0
}
```

---

## 4. Feeding Lines

Gestion de lineas de alimentacion y sus componentes.

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/feeding-lines` | Lista todas las lineas |
| GET | `/feeding-lines/{line_id}` | Obtiene detalle de una linea |
| PATCH | `/feeding-lines/{line_id}/blower` | Actualiza configuracion del blower |
| PATCH | `/feeding-lines/{line_id}/selector` | Actualiza configuracion del selector |
| PATCH | `/feeding-lines/{line_id}/dosers/{doser_id}` | Actualiza configuracion de un doser |
| POST | `/feeding-lines/{line_id}/selector/move-to-slot/{slot}` | Mueve selector a un slot |
| POST | `/feeding-lines/{line_id}/selector/reset-position` | Reinicia posicion del selector |

### GET /feeding-lines
Lista todas las lineas de alimentacion con informacion completa.

**Response:**
```json
{
  "lines": [
    {
      "id": "uuid",
      "name": "Linea 1",
      "blower": { ... },
      "dosers": [ ... ],
      "selector": { ... },
      "sensors": [ ... ],
      "total_cages": 12
    }
  ],
  "total": 1
}
```

### PATCH /feeding-lines/{line_id}/blower
Actualiza configuracion del blower.

**Request Body:**
```json
{
  "name": "Blower Principal",
  "non_feeding_power": 30,
  "current_power": 75,
  "blow_before_feeding_time": 5,
  "blow_after_feeding_time": 10
}
```

### PATCH /feeding-lines/{line_id}/selector
Actualiza configuracion del selector.

**Request Body:**
```json
{
  "name": "Selector A",
  "fast_speed": 80,
  "slow_speed": 40
}
```

### PATCH /feeding-lines/{line_id}/dosers/{doser_id}
Actualiza configuracion de un doser especifico.

**Request Body:**
```json
{
  "name": "Doser 1",
  "assigned_silo_id": "uuid",
  "current_rate": 2.5,
  "dosing_range_min": 0.5,
  "dosing_range_max": 5.0
}
```

---

## 5. Device Control

Control directo de dispositivos (blowers, dosers, selectors, coolers).

### Blowers

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/device-control/blowers/{blower_id}/on` | Enciende blower |
| POST | `/device-control/blowers/{blower_id}/off` | Apaga blower |
| POST | `/device-control/blowers/{blower_id}/set-power` | Establece potencia |

### Dosers

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/device-control/dosers/{doser_id}/on` | Enciende doser |
| POST | `/device-control/dosers/{doser_id}/off` | Apaga doser |
| POST | `/device-control/dosers/{doser_id}/set-rate` | Establece tasa (kg/min) |
| POST | `/device-control/dosers/{doser_id}/set-speed` | Establece velocidad motor (%) |

### Selectors

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/device-control/selectors/{selector_id}/move` | Mueve a slot |
| POST | `/device-control/selectors/{selector_id}/reset` | Resetea posicion |

### Coolers

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/device-control/coolers/{cooler_id}/on` | Enciende cooler |
| POST | `/device-control/coolers/{cooler_id}/off` | Apaga cooler |
| POST | `/device-control/coolers/{cooler_id}/set-power` | Establece potencia |

**Ejemplo - Set Blower Power:**
```json
POST /device-control/blowers/{blower_id}/set-power
{
  "power_percentage": 75
}
```

---

## 6. Sensors

Lecturas y configuracion de sensores.

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/feeding-lines/{line_id}/sensors` | Lista sensores de una linea |
| GET | `/feeding-lines/{line_id}/sensors/readings` | Lecturas en tiempo real |
| PATCH | `/feeding-lines/{line_id}/sensors/{sensor_id}` | Actualiza configuracion |

### GET /feeding-lines/{line_id}/sensors/readings
Obtiene lecturas en tiempo real de todos los sensores.

**Response:**
```json
{
  "line_id": "uuid",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "readings": [
    {
      "sensor_id": "uuid",
      "sensor_type": "TEMPERATURE",
      "value": 24.5,
      "unit": "°C",
      "timestamp": "2025-01-15T10:30:00.000Z",
      "is_warning": false,
      "is_critical": false
    },
    {
      "sensor_id": "uuid",
      "sensor_type": "PRESSURE",
      "value": 0.78,
      "unit": "bar",
      "timestamp": "2025-01-15T10:30:00.000Z",
      "is_warning": false,
      "is_critical": false
    },
    {
      "sensor_id": "uuid",
      "sensor_type": "FLOW",
      "value": 14.8,
      "unit": "m³/min",
      "timestamp": "2025-01-15T10:30:00.000Z",
      "is_warning": false,
      "is_critical": false
    }
  ]
}
```

### PATCH /feeding-lines/{line_id}/sensors/{sensor_id}
Actualiza configuracion de un sensor.

**Request Body:**
```json
{
  "name": "Sensor Temperatura Principal",
  "is_enabled": true,
  "warning_threshold": 30.0,
  "critical_threshold": 40.0
}
```

---

## 7. Cages

Gestion completa de jaulas.

### CRUD

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/cages` | Crea nueva jaula |
| GET | `/cages` | Lista todas las jaulas |
| GET | `/cages/{cage_id}` | Obtiene detalle de jaula |
| PATCH | `/cages/{cage_id}` | Actualiza jaula |
| DELETE | `/cages/{cage_id}` | Elimina jaula |

### Configuracion

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| PATCH | `/cages/{cage_id}/config` | Actualiza configuracion |

### Poblacion

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| PUT | `/cages/{cage_id}/population` | Establece poblacion inicial (siembra) |
| POST | `/cages/{cage_id}/mortality` | Registra mortalidad |
| PATCH | `/cages/{cage_id}/biometry` | Actualiza biometria (peso promedio) |
| POST | `/cages/{cage_id}/harvest` | Registra cosecha |
| POST | `/cages/{cage_id}/adjust` | Ajuste manual de poblacion |

### Historial

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/cages/{cage_id}/history` | Historial de eventos de poblacion |
| GET | `/cages/{cage_id}/biometry` | Historial de biometrias |
| GET | `/cages/{cage_id}/mortality` | Historial de mortalidad |
| GET | `/cages/{cage_id}/config-changes` | Historial de cambios de config |

### POST /cages
Crea una nueva jaula.

**Request Body:**
```json
{
  "name": "Jaula A1",
  "fcr": 1.2,
  "volume_m3": 5000,
  "max_density_kg_m3": 25,
  "transport_time_seconds": 45,
  "blower_power": 70
}
```

### PUT /cages/{cage_id}/population
Establece poblacion inicial (siembra).

**Request Body:**
```json
{
  "fish_count": 50000,
  "avg_weight_grams": 150,
  "event_date": "2025-01-15",
  "note": "Siembra inicial lote 2025-A"
}
```

### POST /cages/{cage_id}/mortality
Registra mortalidad.

**Request Body:**
```json
{
  "dead_count": 50,
  "event_date": "2025-01-20",
  "note": "Mortalidad por temperatura"
}
```

### GET /cages/{cage_id}/history
Obtiene historial de eventos con filtros opcionales.

**Query Parameters:**
- `event_types`: Filtrar por tipos (INITIAL_STOCK, MORTALITY, HARVEST, BIOMETRY, etc.)
- `limit`: Cantidad maxima (default: 50, max: 100)
- `offset`: Desplazamiento para paginacion

---

## 8. Cage Groups

Agrupacion logica de jaulas.

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/cage-groups` | Crea grupo de jaulas |
| GET | `/cage-groups` | Lista grupos con metricas |
| GET | `/cage-groups/{group_id}` | Obtiene detalle de grupo |
| PATCH | `/cage-groups/{group_id}` | Actualiza grupo |
| DELETE | `/cage-groups/{group_id}` | Elimina grupo |

### POST /cage-groups
Crea un nuevo grupo de jaulas.

**Request Body:**
```json
{
  "name": "Sector Norte",
  "cage_ids": ["uuid1", "uuid2", "uuid3"],
  "description": "Jaulas del sector norte del centro"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "name": "Sector Norte",
  "description": "Jaulas del sector norte del centro",
  "cage_ids": ["uuid1", "uuid2", "uuid3"],
  "metrics": {
    "total_population": 150000,
    "total_biomass_kg": 22500,
    "avg_weight_grams": 150,
    "total_volume_m3": 15000,
    "avg_density_kg_m3": 1.5
  },
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

### GET /cage-groups
Lista grupos con filtros.

**Query Parameters:**
- `search`: Busqueda en nombre, descripcion o IDs de jaulas
- `limit`: Cantidad maxima (default: 50, max: 100)
- `offset`: Desplazamiento para paginacion

---

## 9. Silos

Gestion de silos de almacenamiento de alimento.

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/silos` | Lista todos los silos |
| GET | `/silos/{silo_id}` | Obtiene detalle de silo |
| POST | `/silos` | Crea nuevo silo |
| PATCH | `/silos/{silo_id}` | Actualiza silo |
| DELETE | `/silos/{silo_id}` | Elimina silo |

### GET /silos
Lista todos los silos con filtro opcional.

**Query Parameters:**
- `is_assigned`: Filtrar por estado de asignacion (true/false/null)

### POST /silos
Crea un nuevo silo.

**Request Body:**
```json
{
  "name": "Silo Principal",
  "capacity_kg": 10000,
  "stock_level_kg": 5000
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "name": "Silo Principal",
  "capacity_kg": 10000,
  "stock_level_kg": 5000,
  "is_assigned": false,
  "created_at": "2025-01-15T10:00:00Z"
}
```

---

## 10. Foods

Gestion de tipos de alimento.

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/foods` | Lista todos los alimentos |
| GET | `/foods/{food_id}` | Obtiene detalle de alimento |
| POST | `/foods` | Crea nuevo alimento |
| PATCH | `/foods/{food_id}` | Actualiza alimento |
| PATCH | `/foods/{food_id}/toggle-active` | Activa/desactiva alimento |
| DELETE | `/foods/{food_id}` | Elimina alimento |

### GET /foods
Lista alimentos con filtro opcional.

**Query Parameters:**
- `active_only`: Si es true, solo retorna alimentos activos (default: false)

### POST /foods
Crea un nuevo tipo de alimento.

**Request Body:**
```json
{
  "name": "Skretting Nutra HP",
  "provider": "Skretting",
  "code": "SKR-NHP-001",
  "ppk": 850,
  "size_mm": 4.5,
  "active": true
}
```

---

## 11. Alerts

Sistema de alertas y notificaciones.

### Alertas

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/alerts` | Lista alertas con filtros |
| GET | `/alerts/unread/count` | Contador de no leidas |
| GET | `/alerts/counts` | Contadores por tipo |
| PATCH | `/alerts/read-all` | Marcar todas como leidas |
| PATCH | `/alerts/{alert_id}` | Actualizar alerta |
| POST | `/alerts/{alert_id}/read` | Marcar como leida |
| POST | `/alerts/{alert_id}/snooze` | Silenciar alerta |
| DELETE | `/alerts/{alert_id}/snooze` | Quitar silenciamiento |
| GET | `/alerts/snoozed` | Lista alertas silenciadas |
| GET | `/alerts/snoozed/count` | Contador de silenciadas |

### Alertas Programadas

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/alerts/scheduled` | Lista alertas programadas |
| POST | `/alerts/scheduled` | Crea alerta programada |
| PATCH | `/alerts/scheduled/{alert_id}` | Actualiza alerta programada |
| DELETE | `/alerts/scheduled/{alert_id}` | Elimina alerta programada |
| PATCH | `/alerts/scheduled/{alert_id}/toggle` | Activa/desactiva |

### GET /alerts
Lista alertas con filtros.

**Query Parameters:**
- `status`: Filtrar por estado (UNREAD,READ,RESOLVED,ARCHIVED)
- `type`: Filtrar por tipo (CRITICAL,WARNING,INFO,SUCCESS)
- `category`: Filtrar por categoria (SYSTEM,DEVICE,FEEDING,INVENTORY,MAINTENANCE,CONNECTION)
- `search`: Buscar en titulo, mensaje y origen
- `limit`: Cantidad maxima (default: 50, max: 100)
- `offset`: Desplazamiento para paginacion

### POST /alerts/{alert_id}/snooze
Silencia una alerta temporalmente.

**Request Body:**
```json
{
  "duration_days": 7
}
```

### POST /alerts/scheduled
Crea una alerta programada.

**Request Body:**
```json
{
  "title": "Mantenimiento Blower",
  "message": "Revisar filtros del blower principal",
  "type": "WARNING",
  "category": "MAINTENANCE",
  "frequency": "MONTHLY",
  "next_trigger_date": "2025-02-15",
  "days_before_warning": 3,
  "device_id": "uuid",
  "device_name": "Blower Linea 1"
}
```

---

## Codigos de Estado HTTP

| Codigo | Significado |
|--------|-------------|
| 200 | OK - Operacion exitosa |
| 201 | Created - Recurso creado exitosamente |
| 204 | No Content - Eliminacion exitosa |
| 400 | Bad Request - Error de validacion |
| 404 | Not Found - Recurso no encontrado |
| 409 | Conflict - Conflicto (nombre duplicado, recurso en uso) |
| 500 | Internal Server Error - Error del servidor |

---

## Tipos de Enumeraciones

### FeedingMode
- `MANUAL`: Control manual del operador
- `CYCLIC`: Alimentacion ciclica (futuro)
- `PROGRAMMED`: Alimentacion programada (futuro)

### SessionStatus
- `ACTIVE`: Sesion activa
- `CLOSED`: Sesion cerrada (fin del dia)

### OperationStatus
- `RUNNING`: Operacion en curso
- `PAUSED`: Operacion pausada
- `COMPLETED`: Completada automaticamente
- `STOPPED`: Detenida manualmente
- `FAILED`: Fallida por error

### CageStatus
- `AVAILABLE`: Disponible
- `IN_USE`: En uso
- `MAINTENANCE`: En mantenimiento

### AlertType
- `CRITICAL`: Atencion inmediata
- `WARNING`: Requiere seguimiento
- `INFO`: Informacion general
- `SUCCESS`: Operacion exitosa

### AlertStatus
- `UNREAD`: Nueva, no vista
- `READ`: Vista pero no resuelta
- `RESOLVED`: Resuelta
- `ARCHIVED`: Archivada

### AlertCategory
- `SYSTEM`: Sistema general
- `DEVICE`: Dispositivos
- `FEEDING`: Operaciones de alimentacion
- `INVENTORY`: Inventario (silos)
- `MAINTENANCE`: Mantenimiento programado
- `CONNECTION`: Conectividad

### SensorType
- `TEMPERATURE`: Temperatura (°C)
- `PRESSURE`: Presion (bar)
- `FLOW`: Flujo (m³/min)

### DoserType
- `PULSE_DOSER`: Dosificador de pulsos
- `VARI_DOSER`: Dosificador variable
- `SCREW_DOSER`: Dosificador de tornillo

---

*Documento generado: Febrero 2026*
