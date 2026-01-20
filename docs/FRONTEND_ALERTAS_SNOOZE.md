# Resumen de Cambios - API de Alertas y Silos

## Nuevas Funcionalidades para Frontend

### 1. Sistema de Silenciamiento de Alertas (Snooze) 🔕

#### Nuevo Endpoint: Silenciar Alerta
```
POST /api/alerts/{alert_id}/snooze
```

**Request Body:**
```json
{
  "duration_days": 1  // 1 o 7 días
}
```

**Response:**
```json
{
  "message": "Alerta silenciada por 1 día(s)",
  "duration_days": 1
}
```

**Errores:**
- `400 Bad Request`: Si `duration_days` no es 1 o 7, o si la alerta no existe
- `500 Internal Server Error`: Error del servidor

**Comportamiento:**
- Las alertas silenciadas **NO aparecen** en `GET /api/alerts` ni en el contador de no leídas
- Después del período de silenciamiento, la alerta vuelve a aparecer automáticamente
- Si se actualiza el contenido de una alerta silenciada (ej: cambio de nivel), el snooze se remueve automáticamente

---

### 2. Campo Nuevo en AlertDTO

El DTO de alertas ahora incluye un nuevo campo:

```typescript
interface AlertDTO {
  id: string;
  type: string;
  status: string;
  category: string;
  title: string;
  message: string;
  source: string | null;
  timestamp: string; // ISO datetime
  read_at: string | null;
  resolved_at: string | null;
  resolved_by: string | null;
  snoozed_until: string | null; // ⬅️ NUEVO CAMPO (ISO datetime)
  metadata: Record<string, any>;
}
```

**Uso del campo `snoozed_until`:**
- `null`: Alerta NO está silenciada
- `"2026-01-20T10:30:00"`: Alerta silenciada hasta esa fecha/hora (ISO 8601)

---

### 3. Umbrales Configurables de Silos (Futuro)

Aunque no hay endpoints nuevos implementados aún, la base de datos y el backend ya soportan umbrales personalizados por silo:

```typescript
interface SiloDTO {
  // ... campos existentes
  warning_threshold_percentage: number;  // ⬅️ Futuro (default: 20.0)
  critical_threshold_percentage: number; // ⬅️ Futuro (default: 10.0)
}
```

**Estos campos estarán disponibles cuando implementemos:**
- `PATCH /api/silos/{silo_id}/thresholds` (endpoint futuro)

Por ahora, todos los silos usan umbrales por defecto:
- **Warning (Advertencia)**: 20% de capacidad
- **Critical (Crítico)**: 10% de capacidad

---

## Casos de Uso Recomendados para Frontend

### Caso 1: Botón "Silenciar por 1 día"
```typescript
async function snoozeAlertForOneDay(alertId: string) {
  const response = await fetch(`/api/alerts/${alertId}/snooze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ duration_days: 1 })
  });
  
  if (response.ok) {
    // Alerta silenciada exitosamente
    // Refrescar lista de alertas
  }
}
```

### Caso 2: Botón "Silenciar por 1 semana"
```typescript
async function snoozeAlertForOneWeek(alertId: string) {
  const response = await fetch(`/api/alerts/${alertId}/snooze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ duration_days: 7 })
  });
  
  if (response.ok) {
    // Alerta silenciada exitosamente
    // Refrescar lista de alertas
  }
}
```

### Caso 3: Mostrar indicador de alerta silenciada
```typescript
function AlertItem({ alert }: { alert: AlertDTO }) {
  const isSnoozed = alert.snoozed_until !== null;
  const snoozedUntil = isSnoozed ? new Date(alert.snoozed_until!) : null;
  
  return (
    <div className="alert-item">
      <h3>{alert.title}</h3>
      <p>{alert.message}</p>
      
      {isSnoozed && (
        <div className="snooze-badge">
          🔕 Silenciada hasta {snoozedUntil?.toLocaleString()}
        </div>
      )}
      
      {!isSnoozed && (
        <div className="snooze-actions">
          <button onClick={() => snoozeAlertForOneDay(alert.id)}>
            Silenciar 1 día
          </button>
          <button onClick={() => snoozeAlertForOneWeek(alert.id)}>
            Silenciar 1 semana
          </button>
        </div>
      )}
    </div>
  );
}
```

---

## Comportamiento Importante

### Alertas Silenciadas NO Aparecen en:
1. ✅ `GET /api/alerts` (listado de alertas)
2. ✅ `GET /api/alerts/unread/count` (contador de no leídas)
3. ✅ Cualquier listado filtrado de alertas

### Las Alertas Vuelven a Aparecer Cuando:
1. ⏰ Se cumple el período de silenciamiento (`snoozed_until` < now)
2. 🔄 Se actualiza el contenido de la alerta (ej: nivel del silo cambia)

### Background Job
El sistema verifica automáticamente los niveles de silos **cada 5 minutos** y:
- Crea/actualiza alertas para silos con nivel bajo
- Respeta los umbrales configurados de cada silo
- **NO duplica alertas** - actualiza las existentes

---

## UI/UX Recomendado

### 1. En Detalle de Alerta
```
┌─────────────────────────────────────────┐
│ ⚠️ Nivel bajo en Silo A                 │
│ El silo está al 15.2% de capacidad     │
│                                         │
│ [🔕 Silenciar 1 día] [🔕 Silenciar 1 semana] │
└─────────────────────────────────────────┘
```

### 2. Alerta Silenciada
```
┌─────────────────────────────────────────┐
│ ⚠️ Nivel bajo en Silo A                 │
│ 🔕 Silenciada hasta 20/01/2026 10:30   │
│                                         │
│ [🔊 Quitar silencio] (futuro)          │
└─────────────────────────────────────────┘
```

### 3. Badge en Lista de Alertas
```
┌─────────────────────────────────────────┐
│ ⚠️ Nivel bajo en Silo A      🔕 1d     │
│ ⚠️ Error en Blower 2                   │
│ 🔴 Sensor fuera de rango               │
└─────────────────────────────────────────┘
```

---

## Testing

### Probar el Snooze:
1. Crear/tener una alerta activa
2. `POST /api/alerts/{id}/snooze` con `duration_days: 1`
3. Verificar que `GET /api/alerts` ya NO la muestra
4. Verificar que el contador de no leídas disminuyó
5. La alerta volverá a aparecer después de 24 horas automáticamente

### Probar Alertas de Nivel Bajo:
1. `PATCH /api/silos/{id}` con `stock_level_kg` < 20% de capacidad
2. Se debe crear/actualizar automáticamente una alerta WARNING
3. Si `stock_level_kg` < 10%, la alerta cambia a CRITICAL

---

## Notas Técnicas

- **Timestamps:** Todos los datetime están en formato ISO 8601 UTC
- **Validación:** `duration_days` solo acepta `1` o `7`
- **Idempotencia:** Silenciar una alerta ya silenciada actualiza la fecha de `snoozed_until`
- **Cascada:** Las alertas silenciadas se excluyen automáticamente de TODOS los endpoints de listado

---

## Endpoints Sin Cambios

Los siguientes endpoints **NO cambiaron** su comportamiento:

- `GET /api/alerts` - Ahora excluye silenciadas
- `GET /api/alerts/unread/count` - Ahora excluye silenciadas
- `POST /api/alerts/{id}/read` - Sin cambios
- `PATCH /api/alerts/{id}` - Sin cambios
- `PATCH /api/alerts/read-all` - Sin cambios

**Único cambio:** `AlertDTO` incluye campo `snoozed_until`

---

## Ejemplos de Peticiones cURL

### Silenciar alerta por 1 día
```bash
curl -X POST http://localhost:8000/api/alerts/{alert_id}/snooze \
  -H "Content-Type: application/json" \
  -d '{"duration_days": 1}'
```

### Silenciar alerta por 1 semana
```bash
curl -X POST http://localhost:8000/api/alerts/{alert_id}/snooze \
  -H "Content-Type: application/json" \
  -d '{"duration_days": 7}'
```

### Listar alertas (excluye silenciadas)
```bash
curl http://localhost:8000/api/alerts
```

### Obtener contador de no leídas (excluye silenciadas)
```bash
curl http://localhost:8000/api/alerts/unread/count
```

---

¿Necesitas más detalles sobre algún endpoint o caso de uso específico? 🚀
