# Requirements Document: Feeding API Infrastructure Fix

## Introduction

Este documento especifica los requisitos para corregir y estandarizar la implementación de la infraestructura y API de los casos de uso de alimentación (feeding). El sistema actual tiene inconsistencias en la capa de persistencia, modelos de base de datos, endpoints REST y sistema de inyección de dependencias que deben ser corregidos siguiendo los patrones ya establecidos en el proyecto (cage_router, system_layout).

## Glossary

- **FeedingSession**: Agregado raíz que representa una sesión operativa de alimentación (un día de trabajo)
- **FeedingEvent**: Evento de auditoría que registra acciones relevantes en una sesión
- **Repository**: Componente de infraestructura que maneja la persistencia de agregados
- **UseCase**: Componente de aplicación que orquesta la lógica de negocio
- **Router**: Componente de API que expone endpoints REST
- **Dependency Injection**: Sistema de FastAPI para inyectar dependencias en endpoints
- **SQLModel**: ORM utilizado para mapear modelos de dominio a tablas de base de datos
- **AsyncSession**: Sesión asíncrona de SQLAlchemy para operaciones de base de datos
- **PLC**: Controlador Lógico Programable (hardware de control)
- **Simulator**: Implementación en memoria del PLC para desarrollo y testing

## Requirements

### Requirement 1: Corrección de Modelos de Persistencia

**User Story:** Como desarrollador, quiero que los modelos de persistencia de FeedingSession y FeedingEvent sigan el patrón establecido en el proyecto, para mantener consistencia arquitectónica.

#### Acceptance Criteria

1. WHEN se define el modelo FeedingSessionModel THEN el sistema SHALL usar SQLModel con configuración de tabla consistente con otros modelos del proyecto
2. WHEN se define el modelo FeedingEventModel THEN el sistema SHALL establecer una relación foreign key correcta con FeedingSessionModel
3. WHEN se persisten campos JSON THEN el sistema SHALL usar Column(JSONB) de PostgreSQL para campos complejos
4. WHEN se definen índices THEN el sistema SHALL crear índices en line_id y date para optimizar consultas frecuentes
5. WHEN se define la relación entre FeedingSession y FeedingEvent THEN el sistema SHALL usar relationship de SQLAlchemy para navegación bidireccional

### Requirement 2: Corrección de Repositorios

**User Story:** Como desarrollador, quiero que los repositorios de FeedingSession sigan el patrón transaccional establecido, para garantizar consistencia de datos.

#### Acceptance Criteria

1. WHEN el repositorio persiste una sesión THEN el sistema SHALL usar flush en lugar de commit para mantener control transaccional
2. WHEN el repositorio persiste eventos THEN el sistema SHALL guardar eventos en la misma transacción que la sesión
3. WHEN el repositorio reconstruye agregados THEN el sistema SHALL mapear correctamente todos los campos del modelo a value objects del dominio
4. WHEN el repositorio busca sesiones activas THEN el sistema SHALL filtrar por estados CREATED, RUNNING y PAUSED ordenados por fecha descendente
5. WHEN el repositorio maneja errores de persistencia THEN el sistema SHALL propagar excepciones de dominio apropiadas

### Requirement 3: Estandarización de Endpoints REST

**User Story:** Como desarrollador de frontend, quiero que los endpoints de feeding sigan el mismo patrón que cage_router y system_layout, para tener una API consistente.

#### Acceptance Criteria

1. WHEN se define un endpoint POST THEN el sistema SHALL usar status_code apropiado (201 para creación, 200 para operaciones)
2. WHEN se manejan errores en endpoints THEN el sistema SHALL usar bloques try-except con HTTPException y códigos de estado apropiados
3. WHEN se reciben parámetros de ruta THEN el sistema SHALL validar tipos usando anotaciones de FastAPI (UUID, str)
4. WHEN se retornan respuestas THEN el sistema SHALL usar response_model con Pydantic models o diccionarios tipados
5. WHEN se documentan endpoints THEN el sistema SHALL incluir docstrings descriptivos con parámetros y comportamiento

### Requirement 4: Corrección de Inyección de Dependencias

**User Story:** Como desarrollador, quiero que el sistema de inyección de dependencias siga el patrón establecido, para mantener código limpio y testeable.

#### Acceptance Criteria

1. WHEN se definen funciones de dependencia THEN el sistema SHALL usar async def con Depends(get_session) para repositorios
2. WHEN se crean use cases THEN el sistema SHALL inyectar todas las dependencias necesarias (repositorios, servicios)
3. WHEN se definen type aliases THEN el sistema SHALL usar Annotated[Type, Depends(func)] para simplificar firmas de endpoints
4. WHEN se maneja el simulador PLC THEN el sistema SHALL usar un singleton en memoria para mantener estado entre requests
5. WHEN se registran dependencias THEN el sistema SHALL agrupar lógicamente (repositorios, servicios, use cases, type aliases)

### Requirement 5: Migración de Base de Datos

**User Story:** Como administrador del sistema, quiero que las tablas de feeding_sessions y feeding_events existan en la base de datos, para poder persistir sesiones de alimentación.

#### Acceptance Criteria

1. WHEN se ejecuta la migración THEN el sistema SHALL crear la tabla feeding_sessions con todos los campos necesarios
2. WHEN se ejecuta la migración THEN el sistema SHALL crear la tabla feeding_events con foreign key a feeding_sessions
3. WHEN se definen constraints THEN el sistema SHALL establecer ON DELETE CASCADE para eventos cuando se elimina una sesión
4. WHEN se crean índices THEN el sistema SHALL crear índices en line_id, date y session_id para optimizar consultas
5. WHEN se ejecuta rollback THEN el sistema SHALL eliminar las tablas en orden correcto respetando foreign keys

### Requirement 6: Validación de DTOs

**User Story:** Como desarrollador, quiero que los DTOs de feeding tengan validaciones apropiadas, para prevenir datos inválidos en el sistema.

#### Acceptance Criteria

1. WHEN se valida StartFeedingRequest THEN el sistema SHALL verificar que target_amount_kg sea mayor o igual a cero
2. WHEN se valida StartFeedingRequest THEN el sistema SHALL verificar que blower_speed_percentage esté entre 0 y 100
3. WHEN se valida StartFeedingRequest THEN el sistema SHALL verificar que dosing_rate_kg_min sea mayor que cero
4. WHEN se valida UpdateParamsRequest THEN el sistema SHALL permitir campos opcionales con las mismas restricciones
5. WHEN se validan UUIDs THEN el sistema SHALL usar el tipo UUID de Python para validación automática

### Requirement 7: Manejo de Errores Consistente

**User Story:** Como desarrollador de frontend, quiero que los errores de la API sean consistentes y descriptivos, para poder manejarlos apropiadamente.

#### Acceptance Criteria

1. WHEN ocurre un error de validación THEN el sistema SHALL retornar HTTP 400 con mensaje descriptivo
2. WHEN no se encuentra un recurso THEN el sistema SHALL retornar HTTP 404 con mensaje descriptivo
3. WHEN ocurre un error de dominio THEN el sistema SHALL retornar HTTP 400 con el mensaje de la excepción de dominio
4. WHEN ocurre un error inesperado THEN el sistema SHALL retornar HTTP 500 con mensaje genérico sin exponer detalles internos
5. WHEN se capturan excepciones THEN el sistema SHALL usar el mismo patrón de try-except que cage_router

### Requirement 8: Integración con Main Application

**User Story:** Como desarrollador, quiero que el router de feeding esté correctamente registrado en la aplicación principal, para que los endpoints sean accesibles.

#### Acceptance Criteria

1. WHEN se inicia la aplicación THEN el sistema SHALL incluir el feeding_router en la lista de routers registrados
2. WHEN se registra el router THEN el sistema SHALL usar el prefijo /api/v1 consistente con otros routers
3. WHEN se configura el router THEN el sistema SHALL incluir tags apropiados para documentación OpenAPI
4. WHEN se accede a /docs THEN el sistema SHALL mostrar todos los endpoints de feeding en la documentación Swagger
5. WHEN se prueba la aplicación THEN el sistema SHALL poder hacer requests a todos los endpoints de feeding

### Requirement 9: Consistencia con Patrones Existentes

**User Story:** Como desarrollador, quiero que todo el código nuevo siga exactamente los mismos patrones que cage_router y system_layout, para mantener uniformidad en el codebase.

#### Acceptance Criteria

1. WHEN se estructura el código THEN el sistema SHALL seguir el mismo orden de imports que cage_router
2. WHEN se definen funciones de dependencia THEN el sistema SHALL usar los mismos nombres de parámetros (session, use_case)
3. WHEN se manejan transacciones THEN el sistema SHALL usar el mismo patrón de commit/rollback que otros repositorios
4. WHEN se definen response models THEN el sistema SHALL usar Pydantic BaseModel como en otros DTOs
5. WHEN se documenta código THEN el sistema SHALL usar el mismo estilo de docstrings que el resto del proyecto

### Requirement 10: Testing de Infraestructura

**User Story:** Como desarrollador, quiero poder verificar que la infraestructura funciona correctamente, para tener confianza en el sistema.

#### Acceptance Criteria

1. WHEN se ejecutan las migraciones THEN el sistema SHALL crear todas las tablas sin errores
2. WHEN se inicia la aplicación THEN el sistema SHALL cargar todos los routers sin errores de importación
3. WHEN se hace un request a /health THEN el sistema SHALL retornar 200 indicando que la aplicación está funcionando
4. WHEN se accede a /docs THEN el sistema SHALL mostrar la documentación completa sin errores
5. WHEN se prueba manualmente un endpoint THEN el sistema SHALL retornar respuestas válidas según el contrato de la API
