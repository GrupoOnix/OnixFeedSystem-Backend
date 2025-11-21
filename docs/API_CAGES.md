# API de Jaulas - Casos de Uso y Endpoints

Este documento define la implementación de la funcionalidad de gestión de jaulas desde el dominio hasta los endpoints.

---

## Arquitectura de Implementación

```
Domain (Cage) → Use Cases → API Endpoints
```

**Flujo:**

1. **Dominio**: Entidad `Cage` con reglas de negocio
2. **Use Cases**: Orquestación de operaciones
3. **DTOs**: Contratos de entrada/salida
4. **Endpoints**: Exposición HTTP

---

## Casos de Uso (Use Cases)

### **QUERIES (Lectura)**

#### 1. ListCagesUseCase

**Responsabilidad:** Listar todas las jaulas del sistema con filtros opcionales

**Input:**

- `line_id` (opcional): Filtrar por línea de alimentación

**Output:**

- Lista de jaulas con datos básicos

**Lógica:**

1. Consultar repositorio con filtros
2. Mapear entidades a DTOs
3. Retornar lista

**Endpoint:** `GET /api/cages?line_id={line_id}`

---

#### 2. GetCageDetailUseCase

**Responsabilidad:** Obtener información completa de una jaula específica

**Input:**

- `cage_id`: ID de la jaula

**Output:**

- Datos completos de la jaula
- Configuración
- Estadísticas calculadas
- Total de mortalidad (desde mortality_log)

**Lógica:**

1. Obtener Cage del repositorio
2. Calcular estadísticas:
   - `survival_rate = (current_fish_count / initial_fish_count) * 100`
   - `mortality_count = initial_fish_count - current_fish_count`
   - `days_in_cycle = today - created_at`
3. Consultar total de mortalidad registrada
4. Obtener nombres relacionados (line_name, feeding_table_name) via joins
5. Mapear a DTO de respuesta

**Endpoint:** `GET /api/cages/{cage_id}`

---

#### 3. GetCageMortalityHistoryUseCase

**Responsabilidad:** Obtener historial de mortalidad de una jaula

**Input:**

- `cage_id`: ID de la jaula
- `limit` (opcional): Cantidad de registros (default: 50)

**Output:**

- Lista de registros de mortalidad ordenados por fecha

**Lógica:**

1. Consultar `cage_mortality_log` filtrado por `cage_id`
2. Ordenar por `report_datetime` DESC
3. Limitar resultados
4. Mapear a DTO

**Endpoint:** `GET /api/cages/{cage_id}/mortality?limit=20`

---

#### 4. GetCageBiometryHistoryUseCase

**Responsabilidad:** Obtener historial de biometría de una jaula

**Input:**

- `cage_id`: ID de la jaula
- `limit` (opcional): Cantidad de registros (default: 50)

**Output:**

- Lista de registros de biometría ordenados por fecha

**Lógica:**

1. Consultar `cage_biometry_log` filtrado por `cage_id`
2. Ordenar por `sampling_date` DESC
3. Limitar resultados
4. Mapear a DTO

**Endpoint:** `GET /api/cages/{cage_id}/biometry?limit=20`

---

### **COMMANDS (Escritura)**

#### 5. RegisterMortalityUseCase

**Responsabilidad:** Registrar mortalidad de peces para reportes

**Input:**

- `cage_id`: ID de la jaula
- `dead_fish_count`: Cantidad de peces muertos
- `report_datetime`: Fecha/hora del reporte
- `average_weight_g` (opcional): Peso promedio de los muertos
- `note` (opcional): Nota descriptiva
- `user_id` (opcional): Usuario que registra

**Output:**

- ID del registro de mortalidad
- Confirmación

**Lógica:**

1. Obtener Cage del repositorio
2. Validar que la jaula tenga población establecida
3. Llamar a `cage.register_mortality(dead_count)` (solo validación)
4. Crear registro en `cage_mortality_log`
5. Persistir registro
6. Retornar confirmación

**⚠️ IMPORTANTE:** NO modifica `current_fish_count` de la jaula

**Endpoint:** `POST /api/cages/{cage_id}/mortality`

**Request Body:**

```json
{
  "dead_fish_count": 50,
  "report_datetime": "2024-01-15T14:30:00Z",
  "average_weight_g": 480,
  "note": "Mortalidad por enfermedad"
}
```

---

#### 6. RegisterBiometryUseCase

**Responsabilidad:** Registrar biometría y actualizar peso promedio

**Input:**

- `cage_id`: ID de la jaula
- `new_average_weight_g`: Nuevo peso promedio
- `sampled_fish_count`: Cantidad de peces muestreados
- `sampling_date`: Fecha del muestreo
- `note` (opcional): Nota descriptiva
- `user_id` (opcional): Usuario que registra

**Output:**

- ID del registro de biometría
- Peso anterior y nuevo
- Nueva biomasa
- Porcentaje de cambio

**Lógica:**

1. Obtener Cage del repositorio
2. Guardar peso anterior (`old_average_weight`)
3. Llamar a `cage.update_biometry(new_weight)`
4. Crear registro en `cage_biometry_log` con peso anterior y nuevo
5. Persistir Cage actualizado
6. Persistir registro de biometría
7. Calcular y retornar estadísticas

**✅ IMPORTANTE:** SÍ modifica `avg_fish_weight` de la jaula

**Endpoint:** `POST /api/cages/{cage_id}/biometry`

**Request Body:**

```json
{
  "new_average_weight_g": 550,
  "sampled_fish_count": 100,
  "sampling_date": "2024-01-15",
  "note": "Muestreo sector norte"
}
```

---

#### 7. UpdateCageConfigurationUseCase

**Responsabilidad:** Actualizar configuración operacional de la jaula

**Input:**

- `cage_id`: ID de la jaula
- `initial_fish_count` (opcional): Población inicial (solo si no está establecida)
- `initial_average_weight_g` (opcional): Peso inicial (solo si no está establecido)
- `fcr` (opcional): Factor de conversión
- `total_volume_m3` (opcional): Volumen
- `max_density_kg_m3` (opcional): Densidad máxima
- `feeding_table_id` (opcional): Tabla de alimentación
- `transport_time_sec` (opcional): Tiempo de transporte

**Output:**

- Configuración actualizada
- Timestamp de actualización

**Lógica:**

1. Obtener Cage del repositorio
2. Si `initial_fish_count` e `initial_average_weight_g` están presentes:
   - Validar que no estén ya establecidos
   - Llamar a `cage.set_initial_population(fish_count, avg_weight)`
3. Actualizar parámetros de configuración usando setters:
   - `cage.fcr = new_fcr`
   - `cage.total_volume = new_volume`
   - `cage.max_density = new_density`
   - `cage.feeding_table_id = table_id`
   - `cage.transport_time = transport_time`
4. Persistir Cage actualizado
5. Retornar configuración actualizada

**Endpoint:** `PUT /api/cages/{cage_id}/config`

**Request Body:**

```json
{
  "initial_fish_count": 5000,
  "initial_average_weight_g": 500,
  "fcr": 1.2,
  "total_volume_m3": 1500,
  "max_density_kg_m3": 20.0,
  "feeding_table_id": "table-1",
  "transport_time_sec": 120
}
```

---

#### 8. UpdateFishCountUseCase

**Responsabilidad:** Actualizar el conteo de peces (recuentos físicos, ajustes)

**Input:**

- `cage_id`: ID de la jaula
- `new_count`: Nuevo conteo de peces
- `reason` (opcional): Motivo del ajuste
- `user_id` (opcional): Usuario que realiza el ajuste

**Output:**

- Nuevo conteo
- Confirmación

**Lógica:**

1. Obtener Cage del repositorio
2. Llamar a `cage.update_fish_count(new_count)`
3. Opcionalmente registrar ajuste en tabla de auditoría
4. Persistir Cage actualizado
5. Retornar confirmación

**Endpoint:** `PUT /api/cages/{cage_id}/fish-count`

**Request Body:**

```json
{
  "new_count": 4850,
  "reason": "Recuento físico"
}
```

---

## Modelos de Persistencia

### Tabla: `cages`

```sql
CREATE TABLE cages (
    cage_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,

    -- Población
    initial_fish_count INT,
    current_fish_count INT,

    -- Biometría
    avg_fish_weight_g DECIMAL(10,2),

    -- Configuración
    fcr DECIMAL(5,2),
    total_volume_m3 DECIMAL(10,2),
    max_density_kg_m3 DECIMAL(10,2),
    feeding_table_id VARCHAR(50),
    transport_time_sec INT,

    -- Relaciones (referencias de conveniencia)
    line_id VARCHAR(50),
    slot_number INT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (line_id) REFERENCES feeding_lines(id),
    FOREIGN KEY (feeding_table_id) REFERENCES feeding_tables(id)
);
```

**Notas:**

- `biomass_kg` NO se persiste (es calculado)
- `total_food_consumed_kg` NO está aquí (va en otro agregado)
- `last_feeding_time` NO está aquí (va en otro agregado)

---

### Tabla: `cage_mortality_log`

```sql
CREATE TABLE cage_mortality_log (
    mortality_id VARCHAR(50) PRIMARY KEY,
    cage_id VARCHAR(50) NOT NULL,
    dead_fish_count INT NOT NULL,
    report_datetime TIMESTAMP NOT NULL,
    average_weight_g DECIMAL(10,2),
    note TEXT,
    user_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (cage_id) REFERENCES cages(cage_id)
);
```

---

### Tabla: `cage_biometry_log`

```sql
CREATE TABLE cage_biometry_log (
    biometry_id VARCHAR(50) PRIMARY KEY,
    cage_id VARCHAR(50) NOT NULL,
    old_average_weight_g DECIMAL(10,2) NOT NULL,
    new_average_weight_g DECIMAL(10,2) NOT NULL,
    sampled_fish_count INT,
    sampling_date DATE NOT NULL,
    note TEXT,
    user_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (cage_id) REFERENCES cages(cage_id)
);
```

---

## DTOs (Data Transfer Objects)

### Request DTOs

```python
# POST /api/cages/{cage_id}/mortality
class RegisterMortalityRequest:
    dead_fish_count: int
    report_datetime: datetime
    average_weight_g: Optional[float]
    note: Optional[str]

# POST /api/cages/{cage_id}/biometry
class RegisterBiometryRequest:
    new_average_weight_g: float
    sampled_fish_count: int
    sampling_date: date
    note: Optional[str]

# PUT /api/cages/{cage_id}/config
class UpdateCageConfigRequest:
    initial_fish_count: Optional[int]
    initial_average_weight_g: Optional[float]
    fcr: Optional[float]
    total_volume_m3: Optional[float]
    max_density_kg_m3: Optional[float]
    feeding_table_id: Optional[str]
    transport_time_sec: Optional[int]

# PUT /api/cages/{cage_id}/fish-count
class UpdateFishCountRequest:
    new_count: int
    reason: Optional[str]
```

### Response DTOs

```python
# GET /api/cages
class CageListItemResponse:
    cage_id: str
    name: str
    line_id: Optional[str]
    slot_number: Optional[int]
    initial_fish_count: Optional[int]
    current_fish_count: Optional[int]
    biomass_kg: float
    avg_fish_weight_g: Optional[float]

# GET /api/cages/{cage_id}
class CageDetailResponse:
    cage_id: str
    name: str
    status: str
    line_id: Optional[str]
    line_name: Optional[str]
    slot_number: Optional[int]
    initial_fish_count: Optional[int]
    current_fish_count: Optional[int]
    biomass_kg: float
    avg_fish_weight_g: Optional[float]
    created_at: datetime
    updated_at: datetime
    config: CageConfigResponse
    statistics: CageStatisticsResponse

class CageConfigResponse:
    fcr: Optional[float]
    total_volume_m3: Optional[float]
    max_density_kg_m3: Optional[float]
    current_density_kg_m3: Optional[float]
    feeding_table_id: Optional[str]
    feeding_table_name: Optional[str]
    transport_time_sec: Optional[int]

class CageStatisticsResponse:
    days_in_cycle: int
    survival_rate: float
    mortality_count: int
    total_mortality_registered: int  # Suma de mortality_log
```

---

## Ruta de Implementación

### Fase 1: Persistencia

1. Crear migración de Alembic para tabla `cages` actualizada
2. Crear migración para `cage_mortality_log`
3. Crear migración para `cage_biometry_log`
4. Actualizar `CageModel` (SQLModel)
5. Crear `MortalityLogModel` (SQLModel)
6. Crear `BiometryLogModel` (SQLModel)
7. Actualizar `CageRepository`
8. Crear `MortalityLogRepository`
9. Crear `BiometryLogRepository`

### Fase 2: Application Layer

1. Crear DTOs de request
2. Crear DTOs de response
3. Implementar `ListCagesUseCase`
4. Implementar `GetCageDetailUseCase`
5. Implementar `GetCageMortalityHistoryUseCase`
6. Implementar `GetCageBiometryHistoryUseCase`
7. Implementar `RegisterMortalityUseCase`
8. Implementar `RegisterBiometryUseCase`
9. Implementar `UpdateCageConfigurationUseCase`
10. Implementar `UpdateFishCountUseCase`

### Fase 3: API Layer

1. Crear endpoints en `cage_router.py`
2. Conectar endpoints con use cases
3. Agregar validaciones de entrada
4. Agregar manejo de errores
5. Documentar con OpenAPI/Swagger

### Fase 4: Testing

1. Tests unitarios de use cases
2. Tests de integración de repositorios
3. Tests de endpoints (E2E)

---

## Decisiones de Diseño Clave

### 1. Mortalidad NO modifica current_fish_count

- Mortalidad es solo para reportes/estadísticas
- El operador actualiza `current_fish_count` manualmente con recuentos físicos
- Esto permite flexibilidad para ajustes por escapes, robos, etc.

### 2. Biomasa es calculada, NO persistida

- `biomass = current_fish_count * avg_fish_weight / 1000`
- Se calcula en tiempo real
- Evita inconsistencias

### 3. Alimentación NO está en Cage

- `total_food_consumed` y `last_feeding_time` irán en otro agregado
- Cage se enfoca en población y biometría

### 4. Relaciones con FeedingLine

- `line_id` y `slot_number` son referencias de conveniencia
- La fuente de verdad está en FeedingLine (SlotAssignment)
- El repositorio sincroniza ambos lados

### 5. CQRS con Use Cases

- Todas las operaciones (queries y commands) pasan por use cases
- Consistencia y testabilidad
- Punto único para lógica de aplicación
