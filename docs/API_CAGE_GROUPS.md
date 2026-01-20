# API de Grupos de Jaulas (Cage Groups)

## Descripción General

La API de Grupos de Jaulas permite organizar y gestionar conjuntos de jaulas para facilitar operaciones por sectores, zonas o criterios personalizados. Los grupos proporcionan métricas agregadas en tiempo real sobre la población, biomasa y densidad del conjunto.

## Características

- **CRUD Completo**: Crear, listar, obtener, actualizar y eliminar grupos
- **Búsqueda y Filtrado**: Búsqueda por nombre, descripción o IDs de jaulas
- **Paginación**: Soporte para grandes volúmenes de datos
- **Métricas Agregadas**: Cálculo automático de métricas del grupo
- **Membresía Múltiple**: Una jaula puede pertenecer a varios grupos
- **Validación Estricta**: Garantiza integridad de datos

---

## Endpoints

### Base URL
```
/api/cage-groups
```

---

## 1. Crear Grupo de Jaulas

Crea un nuevo grupo de jaulas con las jaulas especificadas.

### Request

```http
POST /api/cage-groups
Content-Type: application/json
```

```json
{
  "name": "Sector Norte",
  "cage_ids": [
    "a22eb4f2-71dc-4129-8379-c736117c39ce",
    "acd25e5e-e46e-419a-904b-ba9e38697258"
  ],
  "description": "Jaulas del sector norte del centro"
}
```

### Request Body Parameters

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `name` | string | Sí | Nombre único del grupo (1-255 caracteres) |
| `cage_ids` | array[string] | Sí | Lista de UUIDs de jaulas (mínimo 1) |
| `description` | string | No | Descripción opcional del grupo |

### Response

**Status**: `201 Created`

```json
{
  "id": "9644488e-f9f9-4476-8fb2-dea4f8316cb3",
  "name": "Sector Norte",
  "description": "Jaulas del sector norte del centro",
  "cage_ids": [
    "acd25e5e-e46e-419a-904b-ba9e38697258",
    "a22eb4f2-71dc-4129-8379-c736117c39ce"
  ],
  "created_at": "2026-01-19T17:37:49.078504",
  "updated_at": "2026-01-19T17:37:49.078509",
  "metrics": {
    "total_population": 9000,
    "total_biomass": 2007.0,
    "avg_weight": 223.0,
    "total_volume": 10000.0,
    "avg_density": 0.2
  }
}
```

### Response Fields

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | string | UUID único del grupo |
| `name` | string | Nombre del grupo |
| `description` | string\|null | Descripción del grupo |
| `cage_ids` | array[string] | Lista de UUIDs de jaulas |
| `created_at` | string | Timestamp de creación (ISO 8601) |
| `updated_at` | string | Timestamp de última actualización (ISO 8601) |
| `metrics` | object | Métricas agregadas del grupo |
| `metrics.total_population` | number | Población total (suma de todas las jaulas) |
| `metrics.total_biomass` | number | Biomasa total en kg |
| `metrics.avg_weight` | number | Peso promedio ponderado en gramos |
| `metrics.total_volume` | number | Volumen total en m³ |
| `metrics.avg_density` | number | Densidad promedio (biomasa/volumen) |

### Error Responses

| Status | Código | Descripción |
|--------|--------|-------------|
| 400 | Bad Request | Datos inválidos |
| 400 | Bad Request | Nombre duplicado |
| 400 | Bad Request | Jaula no existe |

**Ejemplo de error**:
```json
{
  "detail": "Ya existe un grupo con el nombre 'Sector Norte'"
}
```

### Reglas de Negocio

- El nombre debe ser único (case-insensitive)
- Todas las jaulas deben existir en el sistema
- Debe contener al menos 1 jaula
- Una jaula puede pertenecer a múltiples grupos

---

## 2. Listar Grupos de Jaulas

Obtiene una lista paginada de grupos con filtros opcionales.

### Request

```http
GET /api/cage-groups?search=norte&limit=50&offset=0
```

### Query Parameters

| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|------|-----------|---------|-------------|
| `search` | string | No | - | Buscar en nombre, descripción o IDs de jaulas |
| `limit` | integer | No | 50 | Cantidad máxima de resultados (1-100) |
| `offset` | integer | No | 0 | Desplazamiento para paginación |

### Response

**Status**: `200 OK`

```json
{
  "groups": [
    {
      "id": "9644488e-f9f9-4476-8fb2-dea4f8316cb3",
      "name": "Sector Norte",
      "description": "Jaulas del sector norte del centro",
      "cage_ids": [
        "acd25e5e-e46e-419a-904b-ba9e38697258",
        "a22eb4f2-71dc-4129-8379-c736117c39ce"
      ],
      "created_at": "2026-01-19T17:37:49.078504",
      "updated_at": "2026-01-19T17:37:49.078509",
      "metrics": {
        "total_population": 9000,
        "total_biomass": 2007.0,
        "avg_weight": 223.0,
        "total_volume": 10000.0,
        "avg_density": 0.2
      }
    }
  ],
  "total": 1
}
```

### Response Fields

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `groups` | array | Lista de grupos de jaulas |
| `total` | number | Total de grupos que coinciden con los filtros |

### Búsqueda

El parámetro `search` busca coincidencias parciales (case-insensitive) en:
- Nombre del grupo
- Descripción del grupo
- IDs de jaulas (coincidencia exacta)

**Ejemplos**:
- `search=norte` → Busca grupos con "norte" en nombre o descripción
- `search=premium` → Busca "premium" en nombre o descripción
- `search=a22eb4f2-71dc-4129-8379-c736117c39ce` → Busca grupos que contengan esa jaula

---

## 3. Obtener Grupo por ID

Obtiene los datos completos de un grupo específico.

### Request

```http
GET /api/cage-groups/{group_id}
```

### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `group_id` | string | UUID del grupo |

### Response

**Status**: `200 OK`

```json
{
  "id": "9644488e-f9f9-4476-8fb2-dea4f8316cb3",
  "name": "Sector Norte",
  "description": "Jaulas del sector norte del centro",
  "cage_ids": [
    "acd25e5e-e46e-419a-904b-ba9e38697258",
    "a22eb4f2-71dc-4129-8379-c736117c39ce"
  ],
  "created_at": "2026-01-19T17:37:49.078504",
  "updated_at": "2026-01-19T17:37:49.078509",
  "metrics": {
    "total_population": 9000,
    "total_biomass": 2007.0,
    "avg_weight": 223.0,
    "total_volume": 10000.0,
    "avg_density": 0.2
  }
}
```

### Error Responses

| Status | Código | Descripción |
|--------|--------|-------------|
| 404 | Not Found | Grupo no existe |

**Ejemplo de error**:
```json
{
  "detail": "No existe un grupo con ID '00000000-0000-0000-0000-000000000000'"
}
```

---

## 4. Actualizar Grupo de Jaulas

Actualiza uno o más campos de un grupo existente.

### Request

```http
PATCH /api/cage-groups/{group_id}
Content-Type: application/json
```

```json
{
  "name": "Sector Norte Premium",
  "description": "Jaulas principales del sector norte"
}
```

### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `group_id` | string | UUID del grupo a actualizar |

### Request Body Parameters

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `name` | string | No | Nuevo nombre del grupo |
| `cage_ids` | array[string] | No | Nueva lista de IDs de jaulas |
| `description` | string\|null | No | Nueva descripción (null para limpiar) |

**Notas**:
- Solo se actualizan los campos proporcionados
- El campo `updated_at` se actualiza automáticamente
- Se pueden actualizar múltiples campos en una sola petición

### Response

**Status**: `200 OK`

```json
{
  "id": "9644488e-f9f9-4476-8fb2-dea4f8316cb3",
  "name": "Sector Norte Premium",
  "description": "Jaulas principales del sector norte",
  "cage_ids": [
    "acd25e5e-e46e-419a-904b-ba9e38697258",
    "a22eb4f2-71dc-4129-8379-c736117c39ce"
  ],
  "created_at": "2026-01-19T17:37:49.078504",
  "updated_at": "2026-01-19T17:38:00.294006",
  "metrics": {
    "total_population": 9000,
    "total_biomass": 2007.0,
    "avg_weight": 223.0,
    "total_volume": 10000.0,
    "avg_density": 0.2
  }
}
```

### Error Responses

| Status | Código | Descripción |
|--------|--------|-------------|
| 400 | Bad Request | Datos inválidos |
| 400 | Bad Request | Nombre duplicado |
| 400 | Bad Request | Jaula no existe |
| 404 | Not Found | Grupo no existe |

### Reglas de Negocio

- El nuevo nombre debe ser único (excepto si es el mismo nombre actual)
- Todas las jaulas en `cage_ids` deben existir
- Si se proporciona `cage_ids`, debe contener al menos 1 jaula

---

## 5. Eliminar Grupo de Jaulas

Elimina permanentemente un grupo de jaulas.

### Request

```http
DELETE /api/cage-groups/{group_id}
```

### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `group_id` | string | UUID del grupo a eliminar |

### Response

**Status**: `204 No Content`

Sin contenido en el cuerpo de la respuesta.

### Error Responses

| Status | Código | Descripción |
|--------|--------|-------------|
| 404 | Not Found | Grupo no existe |

### Comportamiento

- **Eliminación física (hard delete)**: El registro se elimina permanentemente
- **Las jaulas NO se ven afectadas**: Solo se elimina la agrupación, las jaulas continúan existiendo
- **No es reversible**: La operación no puede deshacerse

---

## Ejemplos de Uso

### Ejemplo 1: Crear grupo y listar

```bash
# 1. Crear grupo
curl -X POST http://localhost:8000/api/cage-groups \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sector Sur",
    "cage_ids": [
      "bc44cf2d-970e-4ff0-b8ae-bef6e0ffdd84",
      "869579ab-c14b-44ac-a77b-10625d3eb1cd"
    ],
    "description": "Jaulas del sector sur"
  }'

# 2. Listar todos los grupos
curl http://localhost:8000/api/cage-groups
```

### Ejemplo 2: Búsqueda y filtrado

```bash
# Buscar grupos que contengan "sur"
curl "http://localhost:8000/api/cage-groups?search=sur"

# Paginación: obtener los siguientes 25 grupos
curl "http://localhost:8000/api/cage-groups?limit=25&offset=25"
```

### Ejemplo 3: Actualizar y obtener

```bash
# 1. Actualizar nombre y descripción
curl -X PATCH http://localhost:8000/api/cage-groups/9644488e-f9f9-4476-8fb2-dea4f8316cb3 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Zona Premium",
    "description": "Jaulas de alto rendimiento"
  }'

# 2. Obtener grupo actualizado
curl http://localhost:8000/api/cage-groups/9644488e-f9f9-4476-8fb2-dea4f8316cb3
```

### Ejemplo 4: Agregar jaulas a un grupo

```bash
# Actualizar la lista de jaulas (reemplaza completamente)
curl -X PATCH http://localhost:8000/api/cage-groups/9644488e-f9f9-4476-8fb2-dea4f8316cb3 \
  -H "Content-Type: application/json" \
  -d '{
    "cage_ids": [
      "a22eb4f2-71dc-4129-8379-c736117c39ce",
      "acd25e5e-e46e-419a-904b-ba9e38697258",
      "bc44cf2d-970e-4ff0-b8ae-bef6e0ffdd84"
    ]
  }'
```

### Ejemplo 5: Eliminar grupo

```bash
# Eliminar grupo permanentemente
curl -X DELETE http://localhost:8000/api/cage-groups/9644488e-f9f9-4476-8fb2-dea4f8316cb3
```

---

## Casos de Uso Comunes

### 1. Organización por Sectores Geográficos

Agrupar jaulas por ubicación física en el centro de cultivo:

```json
{
  "name": "Sector Norte",
  "cage_ids": ["cage-1", "cage-2", "cage-3"],
  "description": "Jaulas ubicadas en el sector norte del centro"
}
```

### 2. Agrupación por Estado de Producción

Crear grupos según el ciclo de producción:

```json
{
  "name": "Fase de Engorde",
  "cage_ids": ["cage-5", "cage-6"],
  "description": "Jaulas en etapa de engorde final"
}
```

### 3. Grupos para Operaciones Específicas

Agrupar jaulas que requieren intervenciones similares:

```json
{
  "name": "Requiere Mantenimiento",
  "cage_ids": ["cage-8", "cage-9"],
  "description": "Jaulas programadas para mantenimiento preventivo"
}
```

### 4. Monitoreo de Métricas Agregadas

Usar los grupos para obtener métricas consolidadas:

```bash
# Obtener métricas del sector norte
curl http://localhost:8000/api/cage-groups/{sector-norte-id}

# La respuesta incluye:
# - Población total del sector
# - Biomasa total
# - Peso promedio
# - Densidad promedio
```

---

## Notas Técnicas

### Cálculo de Métricas

Las métricas se calculan en tiempo real cada vez que se consulta un grupo:

- **total_population**: Suma de la población de todas las jaulas
- **total_biomass**: Suma de la biomasa (kg) de todas las jaulas
- **avg_weight**: Promedio ponderado del peso promedio de las jaulas
- **total_volume**: Suma del volumen (m³) de todas las jaulas
- **avg_density**: Promedio de la densidad (biomasa/volumen) de las jaulas

### Validaciones

1. **Nombre único**: El sistema valida que no exista otro grupo con el mismo nombre (case-insensitive)
2. **Jaulas existentes**: Todas las jaulas en `cage_ids` deben existir en el sistema
3. **Mínimo de jaulas**: Un grupo debe contener al menos 1 jaula
4. **Formato UUID**: Todos los IDs deben ser UUIDs válidos

### Membresía Múltiple

- Una jaula puede pertenecer a múltiples grupos simultáneamente
- Eliminar un grupo NO afecta a las jaulas
- Las jaulas mantienen su independencia y pueden seguir siendo usadas en otros grupos

### Paginación

- **Límite máximo**: 100 registros por página
- **Valor por defecto**: 50 registros
- **Offset**: Comienza en 0

---

## Swagger UI

La documentación interactiva está disponible en:

```
http://localhost:8000/docs
```

Busca la sección **"Cage Groups"** con los 5 endpoints documentados.

---

## Códigos de Estado HTTP

| Código | Descripción |
|--------|-------------|
| 200 | OK - Operación exitosa |
| 201 | Created - Recurso creado exitosamente |
| 204 | No Content - Eliminación exitosa |
| 400 | Bad Request - Datos inválidos o regla de negocio violada |
| 404 | Not Found - Recurso no encontrado |
| 422 | Unprocessable Entity - Error de validación de Pydantic |
| 500 | Internal Server Error - Error del servidor |

---

## Versionamiento

Esta API sigue las convenciones RESTful y está sujeta a versionamiento.

**Versión actual**: v1

**Ruta base**: `/api/cage-groups`

---

## Contacto y Soporte

Para reportar problemas o sugerencias, contacta al equipo de desarrollo.
