# Documentación Técnica: Casos de Uso de Alimentación

**Versión:** 2.0
**Fecha:** Noviembre 2025
**Alcance:** Gestión del ciclo de vida de la alimentación (Start, Stop, Pause, Resume, Update) y monitoreo en tiempo real.

## 🧠 Conceptos Clave de Arquitectura

El sistema implementa una arquitectura donde el **Backend** actúa como orquestador y supervisor ("Jefe de Planificación"), mientras que el **PLC (o simulador)** es el ejecutor autónomo de la lógica de control ("Operador de Maquinaria").

### Modelo de Dominio

1.  **FeedingSession (Aggregate Root):** Representa el "Día Operativo" de una línea de alimentación. Contiene múltiples operaciones y mantiene el estado acumulado del día (`total_dispensed_kg`). Siempre está en estado `ACTIVE` durante el día operativo.

2.  **FeedingOperation (Entity):** Representa una "Visita" individual a una jaula, desde START hasta STOP. Cada operación tiene su propio ciclo de vida (RUNNING, PAUSED, COMPLETED, STOPPED, FAILED) y mantiene su propia historia de eventos.

3.  **IFeedingStrategy (Strategy Pattern):** Componente de lógica pura que traduce la intención del usuario (Manual, Cíclico) a una configuración técnica (`MachineConfiguration`) para el PLC.

4.  **IFeedingMachine (Port/Adapter):** Interfaz asíncrona para comunicarse con el hardware. Envía comandos y lee estados, abstrayendo si es Modbus o Simulación.

5.  **PLC Inteligente:** El PLC recibe una lista de instrucciones "resueltas" (`slot_numbers`, `target`, etc.) y gestiona el bucle de control (motores, tiempos, válvulas) por sí mismo.

### Diferencia entre STOP y PAUSE

- **STOP**: Finaliza la operación actual (cierra la visita). La sesión permanece `ACTIVE` y lista para iniciar una nueva operación.
- **PAUSE**: Congela temporalmente la operación actual. Mantiene la memoria del ciclo para poder reanudar exactamente donde quedó.

---

## 📋 Especificación de Casos de Uso

### [UC-03] Iniciar Alimentación (`StartFeedingUseCase`)

**Descripción:** Inicia una nueva operación de alimentación en una línea específica. Resuelve la configuración física necesaria (traducción Lógica → Física) y delega la ejecución al PLC. Gestiona la creación o reutilización de la sesión diaria y crea una nueva operación.

- **Actor:** Operador
- **Trigger:** Botón "INICIAR" en el Frontend.
- **Precondiciones:**
  - La línea de alimentación existe y no está en estado de error crítico.
  - No hay otra operación activa (`RUNNING` o `PAUSED`) en la misma línea.

**Input (DTO `StartFeedingRequest`):**

- `line_id` (UUID): Identificador de la línea.
- `cage_id` (UUID): Jaula objetivo seleccionada.
- `mode` (Enum): Modo de operación (`MANUAL`, `CYCLIC`, etc.).
- `target_amount_kg` (float): Meta de alimentación (Seguridad/Corte).
- `blower_speed_percentage` (float): Velocidad del soplador.
- `dosing_rate_kg_min` (float): Tasa de dosificación.

**Flujo Principal:**

1.  **Validación:** Verifica que la jaula pertenezca a la línea y que los parámetros estén en rangos seguros.
2.  **Resolución Física:** Consulta al repositorio `FeedingLine` para obtener el `physical_slot` (int) correspondiente al `cage_id` (UUID).
3.  **Gestión de Sesión (Day Boundary):**
    - Busca la sesión activa para `line_id`.
    - Si existe y es de ayer (fecha < hoy), la cierra (`session.close_session()`) y crea una nueva.
    - Si no existe sesión para hoy, crea una nueva `FeedingSession` (siempre en estado `ACTIVE`).
4.  **Estrategia:** Instancia la estrategia adecuada (ej. `ManualFeedingStrategy`) inyectando los parámetros físicos resueltos.
5.  **Creación de Operación:** Llama a `session.start_operation(cage_id, target_slot, strategy, machine_service)`.
    - La sesión valida que no haya operación activa.
    - Crea una nueva `FeedingOperation` con estado `RUNNING`.
    - La operación solicita a la estrategia generar el `MachineConfiguration`.
    - La operación guarda un snapshot de la configuración aplicada.
    - La sesión envía la configuración al PLC vía `IFeedingMachine.send_configuration()`.
    - La operación se registra en `session.operations` y se asigna a `session.current_operation`.
6.  **Persistencia:** Guarda la sesión actualizada (con la nueva operación) en el repositorio.

**Output:**

- `operation_id` (UUID): Identificador de la operación creada.

**Postcondiciones:**

- El PLC inicia la secuencia de alimentación.
- La sesión permanece en estado `ACTIVE`.
- Se crea una nueva operación en estado `RUNNING`.
- Se registra un snapshot de la configuración en la operación para auditoría.

---

### [UC-04] Detener Alimentación (`StopFeedingUseCase`)

**Descripción:** Detiene y finaliza la operación actual, cancelando cualquier saldo pendiente en el PLC. Se considera un fin definitivo de la visita actual. La sesión permanece `ACTIVE` y lista para iniciar una nueva operación.

- **Actor:** Operador
- **Trigger:** Botón "DETENER".

**Input:**

- `line_id` (UUID).

**Flujo Principal:**

1.  **Recuperación:** Obtiene la `FeedingSession` activa para la línea.
2.  **Ejecución:** Llama a `session.stop_current_operation(machine_service)`.
    - Envía comando `STOP` al PLC (resetea contadores temporales y lógica de ciclo del PLC).
    - Marca la operación actual con estado `STOPPED`.
    - Registra evento de finalización en la operación.
    - Libera `session.current_operation` (pasa a `None`).
3.  **Persistencia:** Guarda la sesión con la operación finalizada.

**Postcondiciones:**

- El PLC detiene motores y cierra válvulas inmediatamente.
- La operación queda en estado `STOPPED` con `ended_at` registrado.
- La sesión permanece en estado `ACTIVE` (lista para nueva operación).
- `session.current_operation` es `None`.

---

### [UC-05] Modificar Parámetros en Caliente (`UpdateFeedingParametersUseCase`)

**Descripción:** Permite ajustar variables operativas (velocidad de soplado, tasa de dosificación) de la operación activa sin detener el proceso de alimentación ("Hot Swap").

- **Actor:** Operador
- **Trigger:** Controles de ajuste (+/-) en el Dashboard durante la alimentación.
- **Precondiciones:** Debe existir una operación activa en estado `RUNNING`.

**Input (DTO `UpdateParamsRequest`):**

- `line_id` (UUID).
- `blower_speed` (Optional[float]).
- `dosing_rate` (Optional[float]).

**Flujo Principal:**

1.  **Recuperación:** Obtiene la `FeedingSession` activa para la línea.
2.  **Validación:** Verifica que exista `session.current_operation` y que esté en estado `RUNNING`.
3.  **Reconstrucción:** Reconstruye la estrategia actual a partir del snapshot `operation.applied_config`.
4.  **Aplicación de Cambios:**
    - Crea una **nueva instancia** de estrategia con los valores modificados, manteniendo los que no cambiaron (slot, meta).
5.  **Ejecución:** Llama a `session.update_current_operation_params(new_strategy, machine_service)`.
    - Genera un nuevo `MachineConfiguration`.
    - Calcula el "delta" de cambios para registrar un evento de auditoría.
    - Envía la nueva configuración al PLC (el PLC debe soportar cambio de setpoints en vuelo).
    - Actualiza `operation.applied_config` con la nueva configuración.
    - Registra evento `PARAM_CHANGE` en la operación.
6.  **Persistencia:** Guarda la sesión con la operación actualizada.

**Postcondiciones:**

- El PLC ajusta sus actuadores sin detener el flujo de alimentación.
- Queda un registro de auditoría del cambio en `operation.events`.

---

### [UC-06] Obtener Dashboard de Todas las Líneas (`GetAllLinesDashboardUseCase`)

**Descripción:** Provee una vista consolidada de todas las líneas de alimentación con sus operaciones activas. Permite al operador visualizar el estado global del sistema y seleccionar líneas para operar.

- **Actor:** Sistema / Frontend (Polling).
- **Trigger:** Carga de página de alimentación o intervalo de refresco (1-2s).

**Input:** Ninguno.

**Flujo Principal:**

1.  **Consulta Líneas:** Obtiene todas las líneas de alimentación desde el repositorio.
2.  **Para cada línea:**
    - Consulta la `FeedingSession` activa (si existe).
    - Si existe sesión y tiene `current_operation`:
      - Extrae información de la operación activa (id, jaula, slot, progreso, estado).
    - Si no hay operación activa, devuelve la línea sin operación.
3.  **Consolidación:** Mapea toda la información al DTO `AllLinesDashboardResponse`.

**Output:** JSON con array de líneas, cada una con:

- `line_id` (UUID)
- `line_name` (string)
- `current_operation` (objeto o null):
  - `operation_id` (UUID)
  - `cage_id` (UUID)
  - `target_slot` (int)
  - `target_kg` (float)
  - `dispensed_kg` (float)
  - `status` (string: RUNNING, PAUSED, etc.)
  - `started_at` (datetime)

**Ejemplo de Respuesta:**

```json
{
  "lines": [
    {
      "line_id": "uuid-1",
      "line_name": "Línea 1",
      "current_operation": {
        "operation_id": "uuid-op-1",
        "cage_id": "uuid-cage-1",
        "target_slot": 1,
        "target_kg": 50.0,
        "dispensed_kg": 25.5,
        "status": "Running",
        "started_at": "2025-11-28T08:00:00Z"
      }
    },
    {
      "line_id": "uuid-2",
      "line_name": "Línea 2",
      "current_operation": null
    }
  ]
}
```

---

### [UC-07] Sincronizar Estado de Máquina (`SyncMachineStateUseCase`)

**Descripción:** Proceso en segundo plano ("Heartbeat") que mantiene el "gemelo digital" sincronizado con la realidad física del PLC. Actualiza contadores de alimento, detecta fin de ciclo y gestiona inventario.

- **Actor:** Sistema (Background Task).
- **Trigger:** Timer (cada 1 segundo).

**Estado:** PENDIENTE DE IMPLEMENTACIÓN COMPLETA. Se implementará en fase posterior una vez resuelto el arranque del proceso con start, stop, pause y resume.

**Flujo Simplificado (Actual):**

1.  **Lectura:** Obtiene el `MachineStatus` desde el PLC.
2.  **Recuperación:** Carga la `FeedingSession` activa.
3.  **Sincronización:** Llama a `session.update_from_plc(status)`.
    - Calcula delta de alimento entregado.
    - Actualiza `operation.dispensed` y acumuladores de sesión.
    - Detecta errores del PLC.

**Pendiente:**

- Detección automática de fin de ciclo.
- Gestión de inventario de silos.
- Manejo completo de estados del PLC.

---

### [UC-08] Pausar Alimentación (`PauseFeedingUseCase`)

**Descripción:** Solicita una pausa temporal de la operación actual al PLC. El sistema congela motores pero **mantiene la memoria del ciclo** (dónde iba y cuánto faltaba). La operación puede reanudarse posteriormente.

- **Actor:** Operador
- **Trigger:** Botón "PAUSAR" (`||`).

**Input:**

- `line_id` (UUID).

**Flujo Principal:**

1.  **Recuperación:** Obtiene la `FeedingSession` activa para la línea.
2.  **Validación:** Verifica que exista `current_operation` y que esté en estado `RUNNING`.
3.  **Ejecución:** Llama a `session.pause_current_operation(machine_service)`.
    - Envía comando `PAUSE` al PLC.
    - Cambia `operation.status` a `PAUSED`.
    - Registra evento `PAUSED` en la operación.
4.  **Persistencia:** Guarda la sesión con la operación pausada.

**Postcondiciones:**

- El PLC congela motores y válvulas.
- La operación queda en estado `PAUSED`.
- La sesión permanece en estado `ACTIVE`.
- `session.current_operation` sigue apuntando a la operación pausada.

---

### [UC-09] Reanudar Alimentación (`ResumeFeedingUseCase`)

**Descripción:** Reactiva una operación pausada. **No envía una nueva configuración completa**, sino una señal para continuar la ejecución desde la memoria interna del PLC exactamente donde quedó.

- **Actor:** Operador
- **Trigger:** Botón "REANUDAR" (`▶`).
- **Precondiciones:** Debe existir una operación en estado `PAUSED`.

**Input:**

- `line_id` (UUID).

**Flujo Principal:**

1.  **Recuperación:** Obtiene la `FeedingSession` activa para la línea.
2.  **Validación:** Verifica que exista `current_operation` y que esté en estado `PAUSED`.
3.  **Ejecución:** Llama a `session.resume_current_operation(machine_service)`.
    - Envía comando `RESUME` al PLC.
    - Cambia `operation.status` a `RUNNING`.
    - Registra evento `RESUMED` en la operación.
4.  **Persistencia:** Guarda la sesión con la operación reanudada.

**Postcondiciones:**

- El PLC reanuda motores y válvulas desde donde quedó.
- La operación vuelve a estado `RUNNING`.
- La sesión permanece en estado `ACTIVE`.

---

---

## 🛠️ Entidades y DTOs Relacionados

### Aggregate Root

- **`FeedingSession`** (`src/domain/aggregates/feeding_session.py`):
  - Representa el "Día Operativo" de una línea.
  - Contiene múltiples `FeedingOperation`.
  - Mantiene acumuladores globales (`total_dispensed_kg`, `dispensed_by_slot`).
  - Estado: `ACTIVE` (durante el día) o `CLOSED` (fin del día).

### Entities

- **`FeedingOperation`** (`src/domain/entities/feeding_operation.py`):
  - Representa una "Visita" individual a una jaula.
  - Ciclo de vida: `RUNNING` → `PAUSED` → `RUNNING` → `STOPPED`/`COMPLETED`.
  - Mantiene su propia historia de eventos (`OperationEvent`).
  - Usa Value Objects: `OperationId`, `CageId`, `Weight`.

### Value Objects

- **`OperationId`**: Identificador único de operación.
- **`Weight`**: Representa cantidades de alimento (kg).
- **`CageId`**, **`LineId`**, **`SessionId`**: Identificadores de entidades.

### DTOs de Hardware (`src/domain/dtos/machine_io.py`)

- **`MachineConfiguration`**: Contrato de input al PLC (Modo, Slots, Velocidades, Metas).
- **`MachineStatus`**: Contrato de output del PLC (Estado, Contadores, Posición actual).

### Estrategias (`src/domain/strategies/`)

- **`ManualFeedingStrategy`**: Implementa lógica para alimentación manual con meta definida.

### Interfaces (`src/domain/interfaces.py`)

- **`IFeedingMachine`**: Define `send_configuration`, `get_status`, `pause`, `resume`, `stop`.

---

## 📡 Endpoints de API

### POST /feeding/start

Inicia una nueva operación de alimentación.

**Request Body:**

```json
{
  "line_id": "uuid",
  "cage_id": "uuid",
  "mode": "MANUAL",
  "target_amount_kg": 50.0,
  "blower_speed_percentage": 50.0,
  "dosing_rate_kg_min": 10.0
}
```

**Response:**

```json
{
  "operation_id": "uuid",
  "message": "Feeding operation started successfully"
}
```

### POST /feeding/stop

Detiene la operación actual de una línea.

**Query Params:** `line_id` (UUID)

**Response:**

```json
{
  "message": "Feeding operation stopped"
}
```

### POST /feeding/pause

Pausa temporalmente la operación actual.

**Query Params:** `line_id` (UUID)

**Response:**

```json
{
  "message": "Feeding operation paused"
}
```

### POST /feeding/resume

Reanuda la operación pausada.

**Query Params:** `line_id` (UUID)

**Response:**

```json
{
  "message": "Feeding operation resumed"
}
```

### PUT /feeding/update-params

Actualiza parámetros de la operación activa en caliente.

**Request Body:**

```json
{
  "line_id": "uuid",
  "blower_speed": 60.0,
  "dosing_rate": 12.0
}
```

**Response:**

```json
{
  "message": "Parameters updated successfully"
}
```

### GET /feeding/dashboard

Obtiene el dashboard de todas las líneas con sus operaciones activas.

**Response:**

```json
{
  "lines": [
    {
      "line_id": "uuid-1",
      "line_name": "Línea 1",
      "current_operation": {
        "operation_id": "uuid-op-1",
        "cage_id": "uuid-cage-1",
        "target_slot": 1,
        "target_kg": 50.0,
        "dispensed_kg": 25.5,
        "status": "Running",
        "started_at": "2025-11-28T08:00:00Z"
      }
    },
    {
      "line_id": "uuid-2",
      "line_name": "Línea 2",
      "current_operation": null
    }
  ]
}
```

### GET /feeding/session/{line_id}/operations (FUTURO)

Obtiene el historial de operaciones del día para una línea específica. Se implementará en fase posterior.
