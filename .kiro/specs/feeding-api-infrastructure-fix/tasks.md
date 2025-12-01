# Implementation Plan: Feeding API Infrastructure Fix

- [x] 1. Corregir modelos de persistencia ORM

  - Actualizar FeedingSessionModel con configuración correcta de tabla, foreign keys, índices y relaciones
  - Actualizar FeedingEventModel con foreign key CASCADE y relación bidireccional
  - Usar Column(JSONB) para campos JSON y default_factory para objetos mutables
  - _Requirements: 1.1, 1.2, 1.3, 1.5_

- [ ]\* 1.1 Write unit tests for ORM models

  - Test from_domain() and to_domain() methods
  - Test relationship navigation between FeedingSession and FeedingEvent
  - _Requirements: 1.1, 1.2, 1.5_

- [x] 2. Crear migración de base de datos

  - Crear nueva migración Alembic para feeding_sessions y feeding_events
  - Definir upgrade() con creación de tablas, foreign keys, índices
  - Definir downgrade() con eliminación en orden correcto
  - Ejecutar migración en base de datos local para verificar
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]\* 2.1 Write integration test for migration

  - Test that migration runs without errors
  - Test that tables are created with correct schema
  - Test that indexes exist
  - Test CASCADE delete behavior
  - _Requirements: 5.3, 10.1_

- [x] 3. Corregir repositorio de FeedingSession

  - Actualizar save() para usar flush() en lugar de commit()
  - Corregir manejo de INSERT vs UPDATE usando session.get()
  - Corregir conversión de tipos en dispensed_by_slot (int ↔ str)
  - Usar .value para Enums en event_type
  - Asegurar que \_to_domain() reconstruye correctamente todos los campos
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ]\* 3.1 Write property test for repository round-trip

  - **Property 1: Repository Round-Trip Consistency**
  - **Validates: Requirements 2.3**
  - Generate random valid FeedingSession objects
  - Save to repository and retrieve by ID
  - Verify all fields are equivalent (status, total_dispensed_kg, dispensed_by_slot, applied_strategy_config)

- [ ]\* 3.2 Write property test for active session filtering

  - **Property 2: Active Session Filtering**
  - **Validates: Requirements 2.4**
  - Generate collection of sessions with random statuses
  - Query for active sessions by line_id
  - Verify only CREATED/RUNNING/PAUSED are returned
  - Verify results are ordered by date descending

- [x] 4. Estandarizar router de feeding

  - Reescribir feeding_router.py siguiendo exactamente el patrón de cage_router.py
  - Usar rutas RESTful: /lines/{line_id}/stop en lugar de /stop/{line_id}
  - Implementar mismo patrón de try-except para manejo de errores
  - Separar ValueError (404) de DomainException (400) de Exception (500)
  - Agregar docstrings descriptivos a todos los endpoints
  - Usar códigos HTTP apropiados (201 para POST /start, 200 para otros)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]\* 4.1 Write property test for exception mapping

  - **Property 7: Exception to HTTP Status Mapping**
  - **Validates: Requirements 3.2, 7.1, 7.2, 7.3, 7.4**
  - Test that ValueError maps to 404
  - Test that DomainException maps to 400
  - Test that generic Exception maps to 500

- [ ]\* 4.2 Write integration tests for endpoints

  - Test POST /feeding/start returns 201 with valid request
  - Test POST /feeding/lines/{line_id}/stop returns 200
  - Test POST /feeding/lines/{line_id}/pause returns 200
  - Test POST /feeding/lines/{line_id}/resume returns 200
  - Test PATCH /feeding/lines/{line_id}/parameters returns 200
  - Test error responses return correct status codes
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 8.5, 10.5_

- [x] 5. Corregir sistema de inyección de dependencias

  - Reorganizar dependencies.py en secciones claras (Repositorios, Servicios, Use Cases, Type Aliases)
  - Agregar docstrings a todas las funciones de dependencia
  - Implementar get_machine_service() como singleton correctamente
  - Usar async def con Depends(get_session) para repositorios
  - Crear type aliases con Annotated[Type, Depends(func)]
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]\* 5.1 Write property test for singleton behavior

  - **Property 8: PLC Simulator Singleton**
  - **Validates: Requirements 4.4**
  - Call get_machine_service() multiple times
  - Verify all calls return the same instance (same id())

- [x] 6. Validar y corregir DTOs

  - Verificar que StartFeedingRequest tiene validaciones correctas (ge=0, ge=0 le=100, gt=0)
  - Verificar que UpdateParamsRequest permite campos opcionales con mismas validaciones
  - Asegurar que todos los campos UUID usan tipo UUID de Python
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]\* 6.1 Write property tests for DTO validations

  - **Property 3: DTO Validation - Target Amount**
  - **Validates: Requirements 6.1**
  - Test that target_amount_kg < 0 raises ValidationError

  - **Property 4: DTO Validation - Blower Speed Range**
  - **Validates: Requirements 6.2**
  - Test that blower_speed_percentage outside [0, 100] raises ValidationError

  - **Property 5: DTO Validation - Dosing Rate Positive**
  - **Validates: Requirements 6.3**
  - Test that dosing_rate_kg_min ≤ 0 raises ValidationError

  - **Property 6: Optional Fields Validation**
  - **Validates: Requirements 6.4**
  - Test that UpdateParamsRequest validates optional fields when present

- [x] 7. Integrar router en aplicación principal

  - Verificar que feeding_router está registrado en api/routers/**init**.py
  - Verificar que usa prefijo /api consistente con otros routers
  - Verificar que tiene tags apropiados para documentación OpenAPI
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 8. Checkpoint - Verificar que la aplicación inicia correctamente

  - Ejecutar alembic upgrade head sin errores
  - Iniciar aplicación sin errores de importación
  - Verificar GET /health retorna 200
  - Verificar GET /docs muestra endpoints de feeding
  - Hacer request de prueba a cada endpoint
  - _Requirements: 8.4, 8.5, 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]\* 8.1 Write integration tests for application startup

  - Test that application starts without ImportError
  - Test GET /health returns 200 with {"status": "healthy"}
  - Test GET /docs returns documentation page
  - Test that all feeding endpoints are accessible
  - _Requirements: 8.4, 10.2, 10.3, 10.4_

- [x] 9. Revisión final de consistencia con patrones existentes

  - Verificar que orden de imports sigue el patrón de cage_router
  - Verificar que nombres de parámetros son consistentes (session, use_case)
  - Verificar que manejo de transacciones usa mismo patrón
  - Verificar que response models usan Pydantic BaseModel
  - Verificar que docstrings siguen mismo estilo
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 10. Corregir serialización de Enums en capa de dominio y aplicación

  - Crear función helper para serializar dataclasses con Enums a diccionarios JSON-safe
  - Actualizar FeedingSession.start() para usar serialización correcta de applied_strategy_config
  - Actualizar FeedingSession.update_parameters() para usar serialización correcta
  - Verificar que todos los Enums se convierten a .value antes de guardar en JSONB
  - _Requirements: 11.1, 11.2, 11.3_
