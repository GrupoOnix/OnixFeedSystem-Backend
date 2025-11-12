# Feeding System API - Guía de Inicio Rápido

## 🚀 Levantar el Servidor

### Opción 1: FastAPI CLI (Recomendado - Moderno)

```bash
fastapi dev src/main.py
```

### Opción 2: Usando uvicorn directamente

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Nota**: `fastapi dev` es el comando moderno y más simple. Incluye auto-reload y configuración optimizada para desarrollo.

## 📡 Endpoints Disponibles

Una vez levantado el servidor, accede a:

- **Swagger UI (Interactivo)**: http://localhost:8000/docs
- **ReDoc (Documentación)**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health

## 🧪 Probar el Endpoint

### 1. Verificar que el servidor está corriendo

```bash
curl http://localhost:8000/health
```

**Respuesta esperada:**

```json
{
  "status": "healthy",
  "service": "feeding-system-api"
}
```

### 2. Ver estado del sistema

```bash
curl http://localhost:8000/api/system-layout/status
```

**Respuesta esperada (sistema vacío):**

```json
{
  "status": "ok",
  "aggregates": {
    "feeding_lines": 0,
    "silos": 0,
    "cages": 0
  },
  "details": {
    "lines": [],
    "silos": [],
    "cages": []
  }
}
```

### 3. Crear un layout simple

```bash
curl -X POST http://localhost:8000/api/system-layout \
  -H "Content-Type: application/json" \
  -d '{
    "silos": [
      {
        "id": "temp_silo_1",
        "name": "Silo A",
        "capacity": 1000.0
      }
    ],
    "cages": [
      {
        "id": "temp_cage_1",
        "name": "Jaula 1"
      }
    ],
    "feeding_lines": [
      {
        "id": "temp_line_1",
        "line_name": "Linea Principal",
        "blower_config": {
          "id": "temp_blower_1",
          "name": "Soplador 1",
          "non_feeding_power": 50.0,
          "blow_before_time": 5,
          "blow_after_time": 3
        },
        "dosers_config": [
          {
            "id": "temp_doser_1",
            "name": "Dosificador 1",
            "assigned_silo_id": "temp_silo_1",
            "doser_type": "volumetric",
            "min_rate": 10.0,
            "max_rate": 100.0,
            "current_rate": 50.0
          }
        ],
        "selector_config": {
          "id": "temp_selector_1",
          "name": "Selector 1",
          "capacity": 4,
          "fast_speed": 80.0,
          "slow_speed": 20.0
        },
        "slot_assignments": [
          {
            "slot_number": 1,
            "cage_id": "temp_cage_1"
          }
        ]
      }
    ],
    "relations_data": {},
    "presentation_data": {}
  }'
```

**Respuesta esperada:**

```json
{
  "status": "Sincronización completada",
  "lines_processed": 1,
  "silos_processed": 1,
  "cages_processed": 1
}
```

### 4. Verificar que se crearon los agregados

```bash
curl http://localhost:8000/api/system-layout/status
```

**Respuesta esperada:**

```json
{
  "status": "ok",
  "aggregates": {
    "feeding_lines": 1,
    "silos": 1,
    "cages": 1
  },
  "details": {
    "lines": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Linea Principal"
      }
    ],
    "silos": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "name": "Silo A"
      }
    ],
    "cages": [
      {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "name": "Jaula 1"
      }
    ]
  }
}
```

## 📝 Ejemplos Adicionales

Revisa el archivo `examples/api_requests.http` para más ejemplos de requests, incluyendo:

- ✅ Crear layout completo desde cero
- ✅ Actualizar layout existente
- ✅ Casos de error (validaciones)
- ✅ Resetear sistema

## 🧪 Ejecutar Tests

```bash
# Todos los tests
pytest

# Solo tests de API
pytest src/test/test_api_models.py -v

# Solo tests del use case
pytest src/test/test_sync_system_layout_use_case.py -k asyncio -v
```

## 🏗️ Arquitectura

```
Cliente (Frontend/Postman)
    ↓
FastAPI Router (src/api/routers/system_layout.py)
    ↓
Pydantic Models (src/api/models/system_layout.py)
    ↓
Mapper (src/api/mappers/system_layout_mapper.py)
    ↓
Use Case (src/application/use_cases/sync_system_layout.py)
    ↓
Domain Entities (src/domain/aggregates/)
    ↓
Repositories (src/infrastructure/persistence/mock_repositories.py)
    ↓
In-Memory Storage (Mock - temporal)
```

## 🔧 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'src'"

**Solución**: Asegúrate de ejecutar desde la raíz del proyecto:

```bash
cd /ruta/al/proyecto
python run_server.py
```

### Error: "Address already in use"

**Solución**: El puerto 8000 está ocupado. Usa otro puerto:

```bash
uvicorn src.main:app --reload --port 8001
```

### Error: "No module named 'uvicorn'"

**Solución**: Instala las dependencias:

```bash
pip install -r requirements.txt
```

## 📚 Próximos Pasos

1. ✅ **Completado**: Endpoint de sincronización con repositorios mock
2. ⏳ **Pendiente**: Implementar Unit of Work para transaccionalidad
3. ⏳ **Pendiente**: Implementar repositorios con SQLAlchemy + PostgreSQL
4. ⏳ **Pendiente**: Agregar endpoints CRUD individuales
5. ⏳ **Pendiente**: Implementar casos de uso de operaciones de alimentación

## 🐛 Debugging

Para ver logs detallados:

```bash
uvicorn src.main:app --reload --log-level debug
```

Para usar el debugger de VS Code, crea `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["src.main:app", "--reload", "--port", "8000"],
      "jinja": true
    }
  ]
}
```
