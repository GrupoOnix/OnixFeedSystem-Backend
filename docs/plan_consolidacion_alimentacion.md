# Plan de Consolidación del Módulo de Alimentación

Este documento detalla las tareas necesarias para llevar los casos de uso de alimentación de un estado "funcional en memoria" a un estado "completo, robusto y persistente".

## 1. Estrategias de Alimentación
- [ ] **Actualizar `ManualFeedingStrategy`**:
    - Agregar `target_amount_kg` al constructor.
    - Pasar este valor a `MachineConfiguration`.
    - Asegurar que el PLC (o simulador) respete este límite incluso en modo manual (semiautomático).

## 2. Persistencia y Auditoría (Logs)
- [ ] **Crear Modelo de Eventos (`FeedingEventModel`)**:
    - Crear tabla `feeding_events` en la base de datos.
    - Campos: `id`, `session_id`, `timestamp`, `event_type`, `description`, `details` (JSONB).
- [ ] **Actualizar Repositorio (`FeedingSessionRepository`)**:
    - Modificar el método `save` para que también guarde los eventos pendientes (`session.pop_events()`) en la tabla `feeding_events`.
    - Asegurar transaccionalidad (guardar sesión y eventos atómicamente).
- [ ] **Generar Migraciones**:
    - Crear script de migración Alembic para `feeding_sessions` y `feeding_events`.

## 3. Refinamiento de Casos de Uso (`StartFeedingSessionUseCase`)
- [ ] **Validación de Jaula-Línea**:
    - Implementar validación real para asegurar que la jaula pertenece a la línea solicitada.
- [ ] **Resolución de Slot Físico**:
    - Definir mecanismo robusto para obtener el `slot_number` (desde la entidad `Cage` o `FeedingLine`).
    - Manejar error si la jaula no tiene slot asignado.
- [ ] **Conversión de Unidades**:
    - Implementar conversión de `dosing_rate_kg_min` (Input Usuario) a `doser_speed_percentage` (Input PLC).
    - *Nota: Esto puede requerir una tabla de calibración en el futuro, por ahora una conversión lineal simple o directa es aceptable si se documenta.*
- [ ] **Manejo de Límite Diario**:
    - Refinar la lógica de cierre de sesión diaria (Day Boundary) para que sea robusta (ej: cerrar sesiones viejas automáticamente).

## 4. Exposición API (Endpoints)
- [ ] **Crear Router de Alimentación (`feeding_router.py`)**:
    - `POST /feeding/start`: Iniciar sesión.
    - `POST /feeding/stop`: Detener sesión.
    - `POST /feeding/pause`: Pausar sesión.
    - `POST /feeding/resume`: Reanudar sesión.
    - `PATCH /feeding/parameters`: Actualizar parámetros en caliente.
- [ ] **Conectar con Casos de Uso**:
    - Inyectar dependencias correctamente.
    - Manejar excepciones de dominio y retornarlas como códigos HTTP adecuados (400, 404, 409).

## 5. Verificación Final
- [ ] **Test de Integración**:
    - Ejecutar flujo completo persistiendo en base de datos (usando SQLite en memoria o contenedor de prueba).
    - Verificar que los eventos se guardan y se pueden consultar.
