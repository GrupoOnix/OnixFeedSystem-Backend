# Plan: Registro de Actividad de Jaulas (Logs y Eventos)

## Contexto

La pestaña "Logs y Eventos" en la página de detalle de jaula actualmente muestra datos mock. Este documento describe lo que el backend debe implementar para conectar esa UI con datos reales.

El frontend ya tiene el componente `CageLogsTab.tsx` con la UI completa (filtros, paginación, íconos por tipo). Solo necesita un endpoint real al que conectarse.

---

## 1. Modelo de Datos

### Tabla: `cage_activity_log`

Tabla central que registra todos los eventos relevantes de una jaula. Los eventos se insertan automáticamente desde los servicios existentes (no por el usuario directamente).

```sql
CREATE TABLE cage_activity_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cage_id     UUID NOT NULL REFERENCES cages(id) ON DELETE CASCADE,

    -- Clasificación
    event_type  VARCHAR(30) NOT NULL,   -- Ver enum abajo
    category    VARCHAR(30) NOT NULL,   -- Ver enum abajo

    -- Contenido
    message     TEXT NOT NULL,          -- Descripción legible del evento
    details     TEXT,                   -- Detalle técnico o dato adicional (opcional)

    -- Actor
    actor       VARCHAR(100),           -- Nombre de usuario o "Sistema" si es automático

    -- Referencia opcional a la entidad que originó el evento
    source_entity_type  VARCHAR(30),    -- "feeding_operation", "biometry", "mortality", "config_change", "device"
    source_entity_id    UUID,           -- ID de la entidad relacionada

    -- Timestamp del evento (cuándo ocurrió el hecho, no cuándo se insertó el log)
    event_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices para consultas frecuentes
CREATE INDEX idx_cage_activity_log_cage_id ON cage_activity_log(cage_id);
CREATE INDEX idx_cage_activity_log_event_at ON cage_activity_log(event_at DESC);
CREATE INDEX idx_cage_activity_log_event_type ON cage_activity_log(event_type);
```

### Enum: `event_type`

Mapea directamente a los tipos de íconos/colores del frontend:

| Valor      | Descripción                              | UI (color)  |
|------------|------------------------------------------|-------------|
| `SUCCESS`  | Operación completada exitosamente        | Verde       |
| `INFO`     | Evento informativo, cambio de estado     | Gris        |
| `CONFIG`   | Cambio de configuración                  | Azul        |
| `ALERT`    | Anomalía o condición que requiere atención | Ámbar     |

### Enum: `category`

Indica el dominio del evento:

| Valor           | Descripción                              |
|-----------------|------------------------------------------|
| `FEEDING`       | Operaciones de alimentación              |
| `CONFIG`        | Cambios de configuración de jaula        |
| `BIOMETRY`      | Registros de biometría                   |
| `MORTALITY`     | Registros de mortalidad                  |
| `POPULATION`    | Eventos de población (siembra, cosecha, ajuste) |
| `DEVICE`        | Eventos de dispositivos (sensores, selectores, blower) |
| `SYSTEM`        | Eventos del sistema (conexiones, errores internos) |

---

## 2. Endpoint API

### `GET /cages/{cage_id}/activity-log`

Retorna el registro de actividad paginado de una jaula.

**Query Parameters:**

| Parámetro    | Tipo     | Default | Descripción                                       |
|--------------|----------|---------|---------------------------------------------------|
| `limit`      | integer  | 20      | Máximo 100                                        |
| `offset`     | integer  | 0       |                                                   |
| `event_type` | string   | —       | Filtrar por tipo: `SUCCESS,INFO,CONFIG,ALERT` (separados por coma) |
| `category`   | string   | —       | Filtrar por categoría (separados por coma)        |
| `from_date`  | string   | —       | Filtro de fecha inicio (ISO 8601)                 |
| `to_date`    | string   | —       | Filtro de fecha fin (ISO 8601)                    |

**Response `200 OK`:**

```json
{
  "logs": [
    {
      "id": "uuid",
      "cage_id": "uuid",
      "event_type": "SUCCESS",
      "category": "FEEDING",
      "message": "Operación de alimentación completada",
      "details": "130.2 kg dispensados en 50 minutos",
      "actor": "Sistema",
      "source_entity_type": "feeding_operation",
      "source_entity_id": "uuid",
      "event_at": "2024-01-15T14:32:00Z",
      "created_at": "2024-01-15T14:32:01Z"
    }
  ],
  "pagination": {
    "total": 142,
    "limit": 20,
    "offset": 0,
    "has_next": true,
    "has_previous": false
  }
}
```

**Errores:**

| Código | Condición                              |
|--------|----------------------------------------|
| `404`  | `cage_id` no existe                    |
| `422`  | Parámetros de query inválidos          |

---

## 3. Generación Automática de Eventos

Los logs se insertan automáticamente cuando ocurren acciones en el sistema. No hay endpoint para crearlos manualmente.

### 3.1 Operaciones de Alimentación

| Evento                        | `event_type` | `category` | `message`                                      | `details`                                    |
|-------------------------------|--------------|------------|------------------------------------------------|----------------------------------------------|
| Inicio de operación           | `INFO`       | `FEEDING`  | `"Inicio de operación de alimentación"`       | `"Línea: {line_name}"`                       |
| Operación pausada             | `INFO`       | `FEEDING`  | `"Operación de alimentación pausada"`         | `"{kg_dispensed} kg dispensados hasta ahora"` |
| Operación reanudada           | `INFO`       | `FEEDING`  | `"Operación de alimentación reanudada"`       | —                                            |
| Operación completada          | `SUCCESS`    | `FEEDING`  | `"Operación de alimentación completada"`      | `"{kg_dispensed} kg dispensados en {duration_min} minutos"` |
| Operación detenida manualmente| `INFO`       | `FEEDING`  | `"Operación de alimentación detenida"`        | `"{kg_dispensed} kg dispensados"`            |
| Operación fallida             | `ALERT`      | `FEEDING`  | `"Falla en operación de alimentación"`        | Motivo del fallo si está disponible          |

> **Nota**: El campo `actor` debe ser `"Sistema"` para operaciones automáticas. Si hay un usuario autenticado que inicia/detiene, usar su nombre.

### 3.2 Cambios de Configuración

Cuando se llama `PATCH /cages/{cage_id}/config`, generar un log por cada campo modificado:

| Campo modificado            | `message`                                        | `details`                                       |
|-----------------------------|--------------------------------------------------|-------------------------------------------------|
| `fcr`                       | `"FCR actualizado"`                              | `"Valor anterior: {old} → Nuevo valor: {new}"` |
| `volume_m3`                 | `"Volumen de jaula actualizado"`                 | `"{old} m³ → {new} m³"`                        |
| `max_density_kg_m3`         | `"Densidad máxima actualizada"`                  | `"{old} kg/m³ → {new} kg/m³"`                  |
| `transport_time_seconds`    | `"Tiempo de tránsito actualizado"`               | `"{old}s → {new}s"`                            |
| `blower_power`              | `"Potencia del blower actualizada"`              | `"{old}% → {new}%"`                            |
| `daily_feeding_target_kg`   | `"Objetivo diario de alimentación actualizado"`  | `"{old} kg → {new} kg"`                        |

Todos con `event_type: CONFIG`, `category: CONFIG`.

> **Importante**: Para obtener el valor anterior, leer el registro actual antes de aplicar el `PATCH`. Todos los cambios de una sola request pueden consolidarse en un único log con `details` listando todos los cambios, o generarse uno por campo (preferir uno por campo para mayor granularidad).

### 3.3 Biometría

Al registrar `POST /cages/{cage_id}/biometry`:

```
event_type: INFO
category:   BIOMETRY
message:    "Registro de biometría completado"
details:    "{sampled_count} peces muestreados, peso promedio: {new_weight_kg} kg"
            (o si no hay sampled_count: "Peso promedio actualizado: {old_weight_kg} kg → {new_weight_kg} kg")
actor:      nombre del usuario que registró
source_entity_type: "biometry"
source_entity_id:   ID del registro de biometría creado
```

### 3.4 Mortalidad

Al registrar `POST /cages/{cage_id}/mortality`:

```
event_type: INFO
category:   MORTALITY
message:    "Registro de mortalidad"
details:    "{dead_count} peces" + nota si existe
actor:      nombre del usuario que registró
source_entity_type: "mortality"
source_entity_id:   ID del registro de mortalidad creado
```

### 3.5 Eventos de Población

Al ejecutar cualquier endpoint de población:

| Endpoint               | `message`                              | `event_type` |
|------------------------|----------------------------------------|--------------|
| `set-population`       | `"Siembra inicial registrada"`         | `INFO`       |
| `harvest`              | `"Cosecha registrada"`                 | `INFO`       |
| `adjust-inventory`     | `"Ajuste de inventario registrado"`    | `CONFIG`     |

Para todos: `category: POPULATION`, incluir el `note` del evento en `details` si existe.

### 3.6 Eventos de Dispositivos (opcional, fase 2)

Si el backend detecta desconexiones de dispositivos o alertas de sensores asociados a una jaula, generar logs con:

```
event_type: ALERT
category:   DEVICE
message:    "Pérdida de conexión con selector"  |  "Temperatura fuera de rango"  | etc.
details:    información técnica del evento
actor:      null (evento de sistema)
```

---

## 4. Integración con el Frontend

El frontend ya tiene el componente completamente implementado. Para conectarlo al backend:

### 4.1 Tipos TypeScript a agregar en `cage-api.ts`

```typescript
export type CageActivityLogEventType = "SUCCESS" | "INFO" | "CONFIG" | "ALERT";
export type CageActivityLogCategory =
  | "FEEDING"
  | "CONFIG"
  | "BIOMETRY"
  | "MORTALITY"
  | "POPULATION"
  | "DEVICE"
  | "SYSTEM";

export interface CageActivityLogItem {
  id: string;
  cage_id: string;
  event_type: CageActivityLogEventType;
  category: CageActivityLogCategory;
  message: string;
  details: string | null;
  actor: string | null;
  source_entity_type: string | null;
  source_entity_id: string | null;
  event_at: string; // ISO 8601
  created_at: string; // ISO 8601
}

export interface CageActivityLogResponse {
  logs: CageActivityLogItem[];
  pagination: CagePagination;
}

export interface CageActivityLogParams {
  limit?: number;
  offset?: number;
  event_type?: string; // "SUCCESS,INFO,CONFIG,ALERT"
  category?: string;
  from_date?: string;
  to_date?: string;
}
```

### 4.2 Mapeo de tipos a UI

El `CageLogsTab.tsx` actual usa estos tipos en su UI. El mapeo entre la API y el componente es:

| API `event_type` | UI `LogType` | Ícono          | Color   |
|------------------|--------------|----------------|---------|
| `SUCCESS`        | `success`    | `CheckCircle`  | Verde   |
| `INFO`           | `info`       | `Info`         | Gris    |
| `CONFIG`         | `config`     | `Settings`     | Azul    |
| `ALERT`          | `alert`      | `AlertCircle`  | Ámbar   |

El campo `actor` de la API mapea al campo `user` del componente.

---

## 5. Consideraciones de Implementación

### Orden de implementación sugerido

1. **Crear la tabla** `cage_activity_log` con los índices
2. **Implementar el endpoint** `GET /cages/{cage_id}/activity-log`
3. **Agregar generación de logs** en los servicios existentes:
   - Empezar por configuración (más simple, sin estado)
   - Luego biometría y mortalidad
   - Finalmente operaciones de alimentación (más complejo)
4. **Conectar el frontend** (cambio menor: reemplazar MOCK_LOGS por llamada a la API)

### Retención de datos

- No hay requisito de TTL por ahora; guardar indefinidamente
- Si en el futuro el volumen es alto, considerar particionar por `event_at`

### Valores anteriores en cambios de configuración

Para poder registrar "valor anterior → nuevo valor" en cambios de config, el servicio debe leer el estado actual antes de aplicar el update. Alternativa más simple: el cliente puede enviar los valores anteriores en el body del PATCH (requiere cambio de contrato API), pero es preferible que el backend lo resuelva internamente.

### Consideración sobre `actor`

Si el sistema no tiene autenticación de usuarios todavía, usar siempre `"Sistema"` como actor. Cuando se implemente auth, pasar el usuario autenticado desde el contexto de la request.
