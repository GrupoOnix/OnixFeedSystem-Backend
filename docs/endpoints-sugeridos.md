# Endpoints Sugeridos - Ordenados por Facilidad de Implementación

Este documento lista los endpoints sugeridos para el sistema de alimentación, organizados por dificultad de implementación.

---

## **MUY FÁCIL** ✅ (1-2 horas c/u)
*Ya tienes los repositorios y modelos, solo necesitas el use case y el router*

### **Gestión de Silos (Lectura básica)**

#### 1. GET /api/silos
**Descripción**: Listar todos los silos  
**Componentes necesarios**:
- Repository: ✅ Ya existe `SiloRepository`
- Use Case: ❌ Crear `ListSilosUseCase`
- Router: ❌ Crear endpoint

**Implementación**:
```python
# Similar a ListCagesUseCase
class ListSilosUseCase:
    async def execute(self) -> List[SiloDTO]:
        silos = await self.silo_repo.find_all()
        return [map_to_dto(s) for s in silos]
```

---

#### 2. GET /api/silos/{silo_id}
**Descripción**: Obtener detalles de un silo específico  
**Componentes necesarios**:
- Repository: ✅ `SiloRepository.find_by_id()`
- Use Case: ❌ Crear `GetSiloUseCase`
- Router: ❌ Crear endpoint

**Implementación**: Similar a `GET /api/cages/{cage_id}`

---

### **Gestión de Líneas (Lectura básica)**

#### 3. GET /api/feeding-lines
**Descripción**: Listar todas las líneas de alimentación  
**Componentes necesarios**:
- Repository: ✅ Ya existe `FeedingLineRepository`
- Use Case: ❌ Crear `ListFeedingLinesUseCase`
- Router: ❌ Crear endpoint

**Patrón**: Similar a `ListCagesUseCase`

---

#### 4. GET /api/feeding-lines/{line_id}
**Descripción**: Obtener detalles de una línea específica  
**Componentes necesarios**:
- Repository: ✅ `FeedingLineRepository.find_by_id()`
- Use Case: ❌ Crear `GetFeedingLineUseCase`
- Router: ❌ Crear endpoint

---

### **Sesiones (Lectura básica)**

#### 5. GET /api/feeding/sessions/{session_id}
**Descripción**: Obtener detalles de una sesión específica  
**Componentes necesarios**:
- Repository: ✅ `FeedingSessionRepository.find_by_id()`
- Use Case: ❌ Crear `GetSessionUseCase`
- Router: ❌ Crear endpoint

**Respuesta**: Mapear entidad Session a DTO

---

#### 6. GET /api/feeding/sessions/active
**Descripción**: Listar todas las sesiones activas (todas las líneas)  
**Componentes necesarios**:
- Repository: ✅ Extender `FeedingSessionRepository.find_active_by_line_id()`
- Use Case: ❌ Crear `ListActiveSessionsUseCase`
- Router: ❌ Crear endpoint

**Implementación**:
```python
async def find_all_active(self) -> List[FeedingSession]:
    # Query WHERE status = 'ACTIVE'
```

---

### **Operaciones (Lectura básica)**

#### 7. GET /api/feeding/operations/{operation_id}
**Descripción**: Obtener detalles de una operación específica  
**Componentes necesarios**:
- Repository: ✅ `FeedingOperationRepository.find_by_id()`
- Use Case: ❌ Crear `GetOperationUseCase`
- Router: ❌ Crear endpoint

---

## **FÁCIL** 🟢 (2-4 horas c/u)
*Requiere lógica adicional simple o agregaciones básicas*

### **Silos con lógica**

#### 8. GET /api/silos/{silo_id}/stock-history
**Descripción**: Historial de niveles de stock de un silo  
**Componentes necesarios**:
- Migration: ❌ Crear tabla `silo_stock_history`
- Model: ❌ Crear `SiloStockHistoryModel`
- Repository: ❌ Crear `SiloStockHistoryRepository`
- Use Case: ❌ Crear `ListSiloStockHistoryUseCase`
- Router: ❌ Crear endpoint

**Schema tabla**:
```sql
CREATE TABLE silo_stock_history (
    id UUID PRIMARY KEY,
    silo_id UUID REFERENCES silos(id),
    previous_level_mg BIGINT,
    new_level_mg BIGINT,
    delta_mg BIGINT,
    operation_type VARCHAR(50), -- 'RESTOCK', 'CONSUMPTION', 'ADJUSTMENT'
    timestamp TIMESTAMP,
    note TEXT
);
```

**Patrón**: Similar a `list_biometry` con paginación

---

#### 9. POST /api/silos/{silo_id}/restock
**Descripción**: Registrar reabastecimiento de alimento en un silo  
**Request**:
```json
{
  "amount_kg": 1000,
  "note": "Reabastecimiento semanal"
}
```

**Componentes necesarios**:
- Domain: ❌ Agregar método `Silo.restock(amount: Weight)`
- Use Case: ❌ Crear `RestockSiloUseCase`
- Router: ❌ Crear endpoint

**Lógica**:
1. Validar silo existe
2. Validar nueva cantidad no excede capacidad
3. Actualizar `stock_level`
4. Crear registro en `silo_stock_history`

**Patrón**: Similar a `register_biometry`

---

### **Líneas con estado**

#### 10. GET /api/feeding-lines/{line_id}/status
**Descripción**: Obtener estado actual de una línea  
**Respuesta**:
```json
{
  "line_id": "uuid",
  "line_name": "Linea 1",
  "status": "active", // "idle", "active", "maintenance"
  "current_session_id": "uuid",
  "current_operation": {
    "operation_id": "uuid",
    "cage_id": "uuid",
    "status": "running"
  }
}
```

**Componentes necesarios**:
- Use Case: ❌ Crear `GetLineStatusUseCase`
- Router: ❌ Crear endpoint

**Lógica**:
- Consultar si tiene sesión activa
- Consultar si tiene operación en curso
- Calcular estado: `idle`, `active`, `maintenance`

---

#### 11. PATCH /api/feeding-lines/{line_id}/components
**Descripción**: Actualizar componentes de una línea (blower, dosers, selector)  
**Request**:
```json
{
  "blower_config": { ... },
  "dosers_config": [ ... ],
  "selector_config": { ... }
}
```

**Componentes necesarios**:
- Use Case: ❌ Crear `UpdateLineComponentsUseCase`
- Router: ❌ Crear endpoint

**Lógica**: Reutilizar validaciones de `sync_system_layout`

---

### **Sesiones extendidas**

#### 12. GET /api/feeding/sessions/{session_id}/summary
**Descripción**: Obtener resumen completo de una sesión  
**Componentes necesarios**:
- Use Case: ❌ Crear `GetSessionSummaryUseCase`
- Router: ❌ Crear endpoint

**Implementación**:
```python
# Usa método ya existente en feeding_session.py:217
session = await session_repo.find_by_id(session_id)
summary = session.get_daily_summary()
return summary
```

**Respuesta**:
```json
{
  "session_id": "uuid",
  "date": "2025-01-08T10:00:00Z",
  "status": "Active",
  "total_kg": 125.5,
  "details_by_slot": {
    "1": 45.2,
    "2": 80.3
  },
  "current_operation": { ... }
}
```

---

#### 13. GET /api/feeding/sessions/{session_id}/operations
**Descripción**: Listar todas las operaciones de una sesión (histórico)  
**Componentes necesarios**:
- Repository: ✅ Extender `FeedingOperationRepository`
- Use Case: ❌ Crear `ListSessionOperationsUseCase`
- Router: ❌ Crear endpoint

**Query**:
```python
async def find_by_session_id(
    self, 
    session_id: SessionId, 
    limit: int, 
    offset: int
) -> List[FeedingOperation]:
    # SELECT * FROM feeding_operations 
    # WHERE session_id = ? 
    # ORDER BY start_time DESC 
    # LIMIT ? OFFSET ?
```

**Patrón**: Paginación como `list_biometry`

---

#### 14. GET /api/feeding/sessions/{session_id}/events
**Descripción**: Obtener eventos de una sesión (paginado)  
**Componentes necesarios**:
- Repository: ❌ Crear método en `FeedingSessionRepository`
- Use Case: ❌ Crear `ListSessionEventsUseCase`
- Router: ❌ Crear endpoint

**Query**: Tabla `feeding_events` filtrada por `session_id`

---

#### 15. GET /api/feeding/operations/{operation_id}/events
**Descripción**: Obtener eventos de una operación específica  
**Componentes necesarios**:
- Repository: ❌ Extender `FeedingOperationRepository`
- Use Case: ❌ Crear `ListOperationEventsUseCase`
- Router: ❌ Crear endpoint

**Query**: Tabla `operation_events` filtrada por `operation_id`

---

### **Jaulas extendidas**

#### 16. PATCH /api/cages/{cage_id}/status
**Descripción**: Cambiar estado de una jaula (disponible, en uso, mantenimiento)  
**Request**:
```json
{
  "status": "MAINTENANCE",
  "reason": "Limpieza programada"
}
```

**Componentes necesarios**:
- Migration: ❌ Agregar campo `status` a tabla `cages`
- Domain: ❌ Agregar `status` a entidad `Cage`
- Use Case: ❌ Crear `UpdateCageStatusUseCase`
- Router: ❌ Crear endpoint

---

#### 17. GET /api/cages/{cage_id}/statistics
**Descripción**: Obtener estadísticas calculadas de una jaula  
**Respuesta**:
```json
{
  "cage_id": "uuid",
  "fcr_real": 1.35,
  "current_density_kg_m3": 18.5,
  "mortality_rate_percent": 2.1,
  "total_feed_consumed_kg": 450.0,
  "average_daily_feed_kg": 15.2
}
```

**Componentes necesarios**:
- Use Case: ❌ Crear `GetCageStatisticsUseCase`
- Router: ❌ Crear endpoint

**Lógica**: Cálculos basados en:
- Biometry logs
- Mortality logs
- Feeding operations
- Config changes

---

## **MODERADO** 🟡 (4-8 horas c/u)
*Requiere nuevas entidades, lógica de negocio o agregaciones complejas*

### **Silos avanzado**

#### 18. POST /api/silos
**Descripción**: Crear un nuevo silo  
**Request**:
```json
{
  "name": "Silo 5",
  "capacity_kg": 5000,
  "stock_level_kg": 0
}
```

**Componentes necesarios**:
- Use Case: ❌ Crear `CreateSiloUseCase`
- Router: ❌ Crear endpoint

**Validaciones**:
- Nombre único
- Capacidad > 0
- Stock <= Capacidad

**Patrón**: Similar a creación en `sync_system_layout`

---

#### 19. PATCH /api/silos/{silo_id}
**Descripción**: Actualizar configuración de un silo  
**Request**:
```json
{
  "name": "Silo 5 Renovado",
  "capacity_kg": 6000
}
```

**Componentes necesarios**:
- Use Case: ❌ Crear `UpdateSiloUseCase`
- Router: ❌ Crear endpoint

**Validaciones**:
- Si cambia capacidad, validar con `Silo.capacity.setter` (ya existe)
- Validar no está asignado si es cambio crítico

---

#### 20. DELETE /api/silos/{silo_id}
**Descripción**: Eliminar un silo  
**Componentes necesarios**:
- Use Case: ❌ Crear `DeleteSiloUseCase`
- Router: ❌ Crear endpoint

**Validaciones**:
- Validar `silo.is_assigned == False`
- Opción: Soft delete vs Hard delete

---

### **Sesiones con lógica compleja**

#### 21. POST /api/feeding/sessions/{session_id}/close
**Descripción**: Cerrar sesión al final del día  
**Componentes necesarios**:
- Use Case: ❌ Crear `CloseSessionUseCase`
- Router: ❌ Crear endpoint

**Lógica**:
```python
async def execute(self, session_id: SessionId):
    session = await self.session_repo.find_by_id(session_id)
    if not session:
        raise ValueError("Session not found")
    
    # Usa método existente en feeding_session.py:211
    session.close_session()  # Valida no hay operación activa
    
    await self.session_repo.save(session)
```

---

### **Reportes básicos**

#### 22. GET /api/reports/daily-summary
**Descripción**: Resumen diario de todas las líneas  
**Query params**: `?date=2025-01-08`

**Respuesta**:
```json
{
  "date": "2025-01-08",
  "total_kg_dispensed": 450.2,
  "lines": [
    {
      "line_id": "uuid",
      "line_name": "Linea 1",
      "session_id": "uuid",
      "total_kg": 150.5,
      "operations_count": 3,
      "cages_fed": ["Jaula 101", "Jaula 102"]
    }
  ]
}
```

**Componentes necesarios**:
- Use Case: ❌ Crear `GetDailySummaryUseCase`
- Router: ❌ Crear endpoint

**Lógica**: Agregación de todas las sesiones del día con joins

---

#### 23. GET /api/reports/cage/{cage_id}/feeding-history
**Descripción**: Historial de alimentación de una jaula  
**Query params**: `?start_date=2025-01-01&end_date=2025-01-08&limit=50&offset=0`

**Respuesta**:
```json
{
  "cage_id": "uuid",
  "cage_name": "Jaula 101",
  "total_records": 45,
  "feeding_history": [
    {
      "operation_id": "uuid",
      "session_id": "uuid",
      "date": "2025-01-08T10:30:00Z",
      "dispensed_kg": 45.5,
      "target_kg": 50.0,
      "status": "completed"
    }
  ]
}
```

**Componentes necesarios**:
- Use Case: ❌ Crear `GetCageFeedingHistoryUseCase`
- Router: ❌ Crear endpoint

**Query**: Join `operations` → `sessions` → filtrar por `cage_id`

---

#### 24. GET /api/reports/consumption-by-cage
**Descripción**: Consumo de alimento por jaula en un rango de fechas  
**Query params**: `?start_date=2025-01-01&end_date=2025-01-08`

**Respuesta**:
```json
{
  "period": {
    "start": "2025-01-01",
    "end": "2025-01-08"
  },
  "cages": [
    {
      "cage_id": "uuid",
      "cage_name": "Jaula 101",
      "total_kg": 350.5,
      "operations_count": 24,
      "average_per_day_kg": 50.07
    }
  ]
}
```

**Componentes necesarios**:
- Use Case: ❌ Crear `GetConsumptionByCageUseCase`
- Router: ❌ Crear endpoint

**Query**: Agregación de `dispensed` por `cage_id`

---

### **Logs y auditoría**

#### 25. GET /api/logs/alarms
**Descripción**: Log de alarmas del sistema  
**Query params**: `?line_id=uuid&start_date=2025-01-01&type=ALARM&limit=50`

**Respuesta**:
```json
{
  "total_records": 12,
  "alarms": [
    {
      "event_id": "uuid",
      "timestamp": "2025-01-08T14:23:00Z",
      "line_id": "uuid",
      "type": "ALARM",
      "description": "Error de PLC: Timeout",
      "details": { "error_code": "PLC_TIMEOUT" }
    }
  ]
}
```

**Componentes necesarios**:
- Use Case: ❌ Crear `ListAlarmsUseCase`
- Router: ❌ Crear endpoint

**Query**: Filtrar eventos tipo `ALARM` de `feeding_events`

---

#### 26. GET /api/logs/system-status
**Descripción**: Historial de estados del sistema  
**Componentes necesarios**:
- Use Case: ❌ Crear `ListSystemStatusUseCase`
- Router: ❌ Crear endpoint

**Query**: Eventos tipo `SYSTEM_STATUS` de `feeding_events`

---

## **COMPLEJO** 🔴 (8-16 horas c/u)
*Requiere nueva infraestructura, integraciones o lógica compleja*

### **Reportes avanzados**

#### 27. GET /api/reports/line/{line_id}/performance
**Descripción**: Métricas de rendimiento de una línea  
**Respuesta**:
```json
{
  "line_id": "uuid",
  "period": "2025-01-01 to 2025-01-08",
  "uptime_percent": 94.5,
  "total_operations": 56,
  "successful_operations": 53,
  "failed_operations": 3,
  "average_kg_per_hour": 45.2,
  "efficiency_percent": 87.3
}
```

**Componentes necesarios**:
- Use Case: ❌ Crear `GetLinePerformanceUseCase`
- Router: ❌ Crear endpoint

**Lógica**: 
- Agregaciones complejas multi-tabla
- Cálculo de KPIs: uptime, eficiencia, throughput

---

#### 28. GET /api/reports/silo-consumption
**Descripción**: Consumo de silos por período  
**Respuesta**:
```json
{
  "period": "2025-01-01 to 2025-01-08",
  "silos": [
    {
      "silo_id": "uuid",
      "silo_name": "Silo 1",
      "initial_stock_kg": 4500,
      "final_stock_kg": 3200,
      "consumed_kg": 1300,
      "operations_count": 45
    }
  ]
}
```

**Componentes necesarios**:
- Migration: ❌ Trackear relación `operation → doser → silo`
- Use Case: ❌ Crear `GetSiloConsumptionUseCase`
- Router: ❌ Crear endpoint

**Complejidad**: Requiere relación `operation → doser → silo` para trackear consumo

---

### **Monitoreo en tiempo real**

#### 29. GET /api/monitoring/lines/{line_id}/realtime
**Descripción**: Estado del PLC en tiempo real  
**Respuesta**:
```json
{
  "line_id": "uuid",
  "plc_connected": true,
  "current_status": {
    "is_running": true,
    "total_dispensed_kg": 45.2,
    "blower_speed_percent": 75,
    "doser_speed_percent": 60,
    "has_error": false
  },
  "last_update": "2025-01-08T15:23:45Z"
}
```

**Componentes necesarios**:
- Use Case: ❌ Crear `GetRealtimePLCStatusUseCase`
- Router: ❌ Crear endpoint

**Lógica**: Integración directa con `IFeedingMachine.get_status()`

---

#### 30. GET /api/monitoring/silos/levels
**Descripción**: Niveles de todos los silos en tiempo real  
**Respuesta**:
```json
{
  "timestamp": "2025-01-08T15:24:00Z",
  "silos": [
    {
      "silo_id": "uuid",
      "name": "Silo 1",
      "stock_level_kg": 3200,
      "capacity_kg": 5000,
      "fill_percent": 64.0,
      "is_assigned": true
    }
  ]
}
```

**Componentes necesarios**:
- Use Case: ❌ Crear `GetAllSiloLevelsUseCase`
- Router: ❌ Crear endpoint

**Optimización**: Query optimizada para todos los silos

---

### **Mantenimiento**

#### 31. POST /api/feeding-lines/{line_id}/maintenance/start
**Descripción**: Iniciar modo mantenimiento en una línea  
**Request**:
```json
{
  "reason": "Limpieza semanal",
  "estimated_duration_hours": 2
}
```

**Componentes necesarios**:
- Migration: ❌ Crear tabla `maintenance_logs`
- Model: ❌ Crear `MaintenanceLogModel`
- Domain: ❌ Agregar estado `MAINTENANCE` a `FeedingLine`
- Use Case: ❌ Crear `StartMaintenanceUseCase`
- Router: ❌ Crear endpoint

**Validaciones**:
- No hay sesión activa
- Línea no está ya en mantenimiento

---

#### 32. POST /api/feeding-lines/{line_id}/maintenance/end
**Descripción**: Finalizar modo mantenimiento  
**Request**:
```json
{
  "note": "Limpieza completada exitosamente"
}
```

**Componentes necesarios**:
- Use Case: ❌ Crear `EndMaintenanceUseCase`
- Router: ❌ Crear endpoint

**Lógica**: Cambiar estado y registrar fin

---

#### 33. GET /api/diagnostics/components
**Descripción**: Diagnóstico de componentes (sensores, dosificadores, etc.)  
**Respuesta**:
```json
{
  "timestamp": "2025-01-08T15:30:00Z",
  "lines": [
    {
      "line_id": "uuid",
      "components": {
        "blower": { "status": "OK", "last_check": "..." },
        "dosers": [
          { "id": "uuid", "status": "OK", "silo_assigned": true }
        ],
        "selector": { "status": "OK" },
        "sensors": [
          { "id": "uuid", "type": "PRESSURE", "status": "WARNING", "value": 2.1 }
        ]
      }
    }
  ]
}
```

**Componentes necesarios**:
- Use Case: ❌ Crear `DiagnoseComponentsUseCase`
- Router: ❌ Crear endpoint

**Lógica**: Integración con PLC para estado de componentes

---

#### 34. POST /api/diagnostics/test-connection
**Descripción**: Test de conexión con PLC  
**Respuesta**:
```json
{
  "success": true,
  "latency_ms": 45,
  "plc_version": "v2.3.1",
  "timestamp": "2025-01-08T15:35:00Z"
}
```

**Componentes necesarios**:
- Use Case: ❌ Crear `TestPLCConnectionUseCase`
- Router: ❌ Crear endpoint

**Lógica**: Llamada a `IFeedingMachine.health_check()`

---

### **Integración PLC**

#### 35. POST /api/plc/sync
**Descripción**: Sincronizar estado con PLC (bidireccional)  
**Componentes necesarios**:
- Use Case: ❌ Crear `SyncPLCStateUseCase`
- Router: ❌ Crear endpoint

**Complejidad**: 
- Sincronización bidireccional
- Resolución de conflictos
- Manejo de desconexiones

---

#### 36. POST /api/plc/emergency-stop
**Descripción**: Detención de emergencia en todas las líneas  
**Request**:
```json
{
  "reason": "Emergencia: Fuga de agua detectada"
}
```

**Componentes necesarios**:
- Use Case: ❌ Crear `EmergencyStopUseCase`
- Router: ❌ Crear endpoint

**Lógica**:
- Broadcast a todas las líneas
- Llamar `machine.stop()` en todas
- Logging crítico
- Notificaciones

---

#### 37. GET /api/plc/health
**Descripción**: Estado de salud de la conexión PLC  
**Respuesta**:
```json
{
  "overall_status": "HEALTHY",
  "lines": [
    {
      "line_id": "uuid",
      "plc_connected": true,
      "last_heartbeat": "2025-01-08T15:40:00Z",
      "connection_quality": "GOOD"
    }
  ]
}
```

**Componentes necesarios**:
- Infrastructure: ❌ Health check periódico
- Use Case: ❌ Crear `GetPLCHealthUseCase`
- Router: ❌ Crear endpoint

---

## **MUY COMPLEJO** ⚠️ (16+ horas c/u)
*Requiere arquitectura nueva, WebSockets, o features transversales*

### **Tiempo real con WebSockets**

#### 38. WebSocket /ws/feeding/live
**Descripción**: Stream de eventos en vivo  
**Eventos transmitidos**:
- Inicio/detención de operaciones
- Cambios de parámetros
- Alarmas
- Actualizaciones de kg dispensados

**Componentes necesarios**:
- Infrastructure: ❌ WebSocket manager con FastAPI
- Use Case: ❌ Event broadcaster
- Router: ❌ WebSocket endpoint

**Arquitectura**:
```python
from fastapi import WebSocket

class FeedingWebSocketManager:
    active_connections: List[WebSocket] = []
    
    async def broadcast(self, event: Dict):
        # Broadcast a todos los clientes conectados
```

**Complejidad**:
- Manejo de conexiones concurrentes
- Autenticación por WebSocket
- Heartbeat y reconexión
- Event sourcing

---

### **Gestión de usuarios** (si no existe auth)

#### 39. GET /api/users
#### 40. POST /api/users
#### 41. PATCH /api/users/{user_id}/role
#### 42. GET /api/audit-log

**Descripción**: Sistema completo de autenticación y autorización  

**Componentes necesarios**:
- Migration: ❌ Tablas `users`, `roles`, `permissions`, `audit_log`
- Infrastructure: ❌ JWT authentication
- Middleware: ❌ Authorization middleware
- Use Cases: ❌ CRUD usuarios, roles, permisos

**Arquitectura**:
```python
# Middleware de autenticación
from fastapi import Depends
from jose import JWTError, jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Validar JWT
    # Retornar usuario autenticado
```

**Complejidad**: Sistema completo transversal

---

### **Configuración avanzada**

#### 43. GET /api/system/config
#### 44. PATCH /api/system/config

**Descripción**: Gestión de configuración global del sistema  

**Componentes necesarios**:
- Migration: ❌ Tabla `system_config`
- Domain: ❌ Value Objects para configs
- Use Cases: ❌ Get/Update config
- Infrastructure: ❌ Hot reload de configs

**Complejidad**: Validaciones complejas, hot reload

---

### **Tablas de alimentación**

#### 45. GET /api/feeding-tables
#### 46. POST /api/feeding-tables
#### 47. GET /api/feeding-tables/{table_id}/rules

**Descripción**: Motor de reglas de alimentación  

**Componentes necesarios**:
- Migration: ❌ Tablas `feeding_tables`, `feeding_rules`
- Domain: ❌ Nuevo agregado `FeedingTable`
- Use Cases: ❌ CRUD completo
- Business Logic: ❌ Motor de cálculo de raciones

**Ejemplo regla**:
```json
{
  "table_id": "uuid",
  "rules": [
    {
      "condition": "fish_weight_g BETWEEN 100 AND 200",
      "fcr": 1.2,
      "feeding_rate_percent": 2.5
    }
  ]
}
```

**Complejidad**: Motor de reglas completo

---

### **Scheduling**

#### 48. GET /api/cages/{cage_id}/feeding-schedule

**Descripción**: Sistema de programación de alimentación  

**Componentes necesarios**:
- Migration: ❌ Tabla `feeding_schedules`
- Infrastructure: ❌ Background scheduler (APScheduler)
- Use Cases: ❌ CRUD schedules
- Worker: ❌ Cron jobs

**Complejidad**: Scheduler background, cron expressions

---

## **ROADMAP DE IMPLEMENTACIÓN SUGERIDO**

### **Sprint 1 - Quick Wins** (1-2 semanas)
**Objetivo**: MVP de consultas básicas

**Endpoints a implementar**:
1. GET /api/silos
2. GET /api/silos/{silo_id}
3. GET /api/feeding-lines
4. GET /api/feeding-lines/{line_id}
5. GET /api/feeding/sessions/{session_id}
6. GET /api/feeding/sessions/active
7. GET /api/feeding/operations/{operation_id}

**Estimación**: 7-14 horas total

---

### **Sprint 2 - Funcionalidad Core** (2-3 semanas)
**Objetivo**: Gestión de stock y eventos

**Endpoints a implementar**:
8. GET /api/silos/{silo_id}/stock-history
9. POST /api/silos/{silo_id}/restock
10. GET /api/feeding-lines/{line_id}/status
11. PATCH /api/feeding-lines/{line_id}/components
12. GET /api/feeding/sessions/{session_id}/summary
13. GET /api/feeding/sessions/{session_id}/operations
14. GET /api/feeding/sessions/{session_id}/events
15. GET /api/feeding/operations/{operation_id}/events
16. PATCH /api/cages/{cage_id}/status
17. GET /api/cages/{cage_id}/statistics

**Estimación**: 20-40 horas total

---

### **Sprint 3 - Reportes y Analytics** (3-4 semanas)
**Objetivo**: Reportes y gestión completa de silos

**Endpoints a implementar**:
18. POST /api/silos
19. PATCH /api/silos/{silo_id}
20. DELETE /api/silos/{silo_id}
21. POST /api/feeding/sessions/{session_id}/close
22. GET /api/reports/daily-summary
23. GET /api/reports/cage/{cage_id}/feeding-history
24. GET /api/reports/consumption-by-cage
25. GET /api/logs/alarms
26. GET /api/logs/system-status

**Estimación**: 36-72 horas total

---

### **Sprint 4 - Features Avanzados** (4-6 semanas)
**Objetivo**: Monitoreo y mantenimiento

**Endpoints a implementar (según prioridad de negocio)**:
27. GET /api/reports/line/{line_id}/performance
28. GET /api/reports/silo-consumption
29. GET /api/monitoring/lines/{line_id}/realtime
30. GET /api/monitoring/silos/levels
31. POST /api/feeding-lines/{line_id}/maintenance/start
32. POST /api/feeding-lines/{line_id}/maintenance/end
33. GET /api/diagnostics/components
34. POST /api/diagnostics/test-connection
35. POST /api/plc/sync
36. POST /api/plc/emergency-stop
37. GET /api/plc/health

**Estimación**: 88-176 horas total

---

### **Sprint 5+ - Enterprise Features** (6+ semanas)
**Objetivo**: Features empresariales avanzados

**Endpoints a implementar (solo si es necesario)**:
38. WebSocket /ws/feeding/live
39-42. Sistema de usuarios completo
43-44. Configuración del sistema
45-47. Tablas de alimentación
48. Scheduling

**Estimación**: 160+ horas total

---

## **RECOMENDACIÓN INICIAL**

### **Para empezar YA** (Semana 1-2)

Implementa estos **10 endpoints** para tener valor inmediato:

1. ✅ GET /api/silos
2. ✅ GET /api/silos/{silo_id}
3. ✅ GET /api/feeding-lines
4. ✅ GET /api/feeding-lines/{line_id}
5. ✅ GET /api/feeding/sessions/active
6. ✅ GET /api/feeding/sessions/{session_id}/summary
7. ✅ POST /api/silos/{silo_id}/restock
8. ✅ GET /api/feeding-lines/{line_id}/status
9. ✅ GET /api/reports/daily-summary
10. ✅ POST /api/feeding/sessions/{session_id}/close

**Valor entregado**:
- Visualización de todo el sistema
- Gestión básica de stock
- Dashboard de operaciones
- Cierre de sesiones

**Tiempo estimado**: 15-25 horas total

---

## **NOTAS DE IMPLEMENTACIÓN**

### **Patrones a seguir**

1. **Use Cases**: Todos deben heredar patrón existente
2. **DTOs**: Crear en `application/dtos/`
3. **Dependency Injection**: Agregar en `api/dependencies.py`
4. **Error Handling**: Seguir patrón de `HTTPException` existente
5. **Paginación**: Usar patrón de `limit/offset` como biometry
6. **Validaciones**: Usar excepciones de dominio

### **Testing**

Para cada endpoint nuevo:
- ✅ Test unitario del use case
- ✅ Test de integración del endpoint
- ✅ Validar manejo de errores

### **Documentación**

Cada endpoint debe tener:
- ✅ Docstring con descripción
- ✅ Parámetros documentados
- ✅ Ejemplos de request/response
- ✅ Auto-documentación en Swagger (/docs)

---

## **CONCLUSIÓN**

Este roadmap te proporciona:
- **48 endpoints** organizados por complejidad
- **Estimaciones** realistas de tiempo
- **Sprints** sugeridos para implementación incremental
- **Quick wins** para valor inmediato

**Siguiente paso recomendado**: Implementar los 10 endpoints de "Para empezar YA" y obtener feedback del equipo antes de continuar con los siguientes sprints.
