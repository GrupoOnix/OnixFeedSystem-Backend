# Plan: Agregar Campos Faltantes a la Respuesta de List Cages

## Objetivo

Agregar los campos de configuración y estado que existen en el modelo pero no se están enviando en la respuesta del endpoint de listado de jaulas.

## Campos a Agregar

Los siguientes campos ya existen en el modelo de persistencia y dominio, pero no se incluyen en el DTO de respuesta:

- `created_at` / `seeding_date` - Fecha de siembra para calcular días en ciclo
- `volume_m3` - Volumen total de la jaula en metros cúbicos
- `max_density_kg_m3` - Umbral de alarma de densidad
- `fcr` - Factor de Conversión de Alimento
- `feeding_table_id` - ID de la tabla de alimentación asignada
- `transport_time_seconds` - Tiempo de transporte del alimento
- `status` - Estado actual de la jaula

## Tareas

### 1. Actualizar DTO de Respuesta

**Archivo:** `src/application/dtos/cage_dtos.py`

- [ ] Agregar campo `created_at: datetime` a `CageListItemResponse`
- [ ] Agregar campo `volume_m3: Optional[float]` a `CageListItemResponse`
- [ ] Agregar campo `max_density_kg_m3: Optional[float]` a `CageListItemResponse`
- [ ] Agregar campo `fcr: Optional[float]` a `CageListItemResponse`
- [ ] Agregar campo `feeding_table_id: Optional[str]` a `CageListItemResponse`
- [ ] Agregar campo `transport_time_seconds: Optional[int]` a `CageListItemResponse`
- [ ] Agregar campo `status: str` a `CageListItemResponse`

### 2. Actualizar Use Case

**Archivo:** `src/application/use_cases/cage/list_cages_use_case.py`

- [ ] Modificar el mapeo de `Cage` a `CageListItemResponse` para incluir `created_at`
- [ ] Modificar el mapeo para incluir `volume_m3` (convertir desde `total_volume`)
- [ ] Modificar el mapeo para incluir `max_density_kg_m3` (convertir desde `max_density`)
- [ ] Modificar el mapeo para incluir `fcr`
- [ ] Modificar el mapeo para incluir `feeding_table_id`
- [ ] Modificar el mapeo para incluir `transport_time_seconds` (convertir desde `transport_time`)
- [ ] Modificar el mapeo para incluir `status`

### 3. Verificar Dominio

**Archivo:** `src/domain/aggregates/cage.py`

- [ ] Verificar que la propiedad `_created_at` sea accesible (agregar property si falta)
- [ ] Verificar que todas las propiedades necesarias tengan getters públicos

### 4. Verificar Modelo de Persistencia

**Archivo:** `src/infrastructure/persistence/models/cage_model.py`

- [ ] Verificar que el método `to_domain()` mapee correctamente todos los campos
- [ ] Verificar que el método `from_domain()` mapee correctamente todos los campos

### 5. Verificar Repositorio

**Archivo:** `src/infrastructure/persistence/repositories/cage_repository.py`

- [ ] Verificar que el método `list()` retorne todos los campos necesarios
- [ ] Verificar que no haya filtros que excluyan campos

### 6. Testing

**Archivos:** `src/test/application/use_cases/cage/test_list_cages_use_case.py`

- [ ] Actualizar tests existentes para verificar los nuevos campos
- [ ] Agregar assertions para cada nuevo campo en la respuesta

### 7. Documentación API

**Archivo:** `docs/API_CAGES.md` o similar

- [ ] Actualizar la documentación del endpoint con los nuevos campos de respuesta
- [ ] Agregar descripción de cada campo nuevo

## Notas

- **Campos excluidos intencionalmente:**

  - `last_feeding_time` - No implementado aún (requiere sistema de alimentación)
  - `capacity` - Error del frontend, no es necesario
  - `feeding_table_name` - Requiere join con tabla que no existe aún

- **Conversiones necesarias:**
  - `total_volume` (dominio) → `volume_m3` (DTO)
  - `max_density` (dominio) → `max_density_kg_m3` (DTO)
  - `transport_time` (dominio) → `transport_time_seconds` (DTO)
  - `status` (enum) → `status` (string)

## Orden de Implementación Recomendado

1. Actualizar DTO (define el contrato)
2. Verificar/actualizar Dominio (asegurar acceso a datos)
3. Actualizar Use Case (implementar mapeo)
4. Verificar Modelo y Repositorio (asegurar persistencia correcta)
5. Actualizar Tests
6. Actualizar Documentación
