# Estrategia de Testing

Este documento describe la estrategia de testing del sistema de alimentación de peces, basada en los tests implementados.

---

## 🎯 Qué se prueba

### Casos de Uso (Application Layer)

**Ubicación**: `src/test/application/use_cases/`

**Qué se prueba**:

- ✅ Todos los flujos de éxito (happy path)
- ✅ Todos los flujos de error (reglas de negocio FA1-FA7)
- ✅ Casos borde (BD vacía, valores límite)
- ✅ Mapeo de IDs temporales a reales
- ✅ Consistencia entre operaciones (Sync ↔ Get)

**Qué NO se prueba**:

- ❌ Detalles de implementación interna
- ❌ Métodos privados directamente
- ❌ Logs o mensajes de consola
- ❌ Formato específico de errores (solo que falle)

**Archivos de test**:

- `test_sync_system_layout.py` - Operaciones CRUD básicas (13 tests)
- `test_sync_business_rules.py` - Reglas FA3-FA7 y validaciones (14 tests)
- `test_get_system_layout.py` - Lectura y consistencia (6 tests)

---

### Dominio (Domain Layer)

**Ubicación**: Integrado en tests de casos de uso

**Qué se prueba**:

- ✅ Reglas de negocio (invariantes)
- ✅ Validaciones de Value Objects
- ✅ Comportamiento de Aggregate Roots
- ✅ Eventos de dominio (implícito)

**Cómo se prueba**:

- A través de los casos de uso (no tests unitarios aislados)
- Las reglas del dominio se validan al ejecutar operaciones completas
- Los VOs se validan al crear entidades

**Ejemplos**:

- FA1 (Composición mínima): Se prueba al crear líneas sin componentes
- FA5 (Silo 1-a-1): Se prueba al asignar silo a múltiples dosificadores
- Weight (no negativo): Se prueba al crear silos con capacidad negativa

---

### Infraestructura (Infrastructure Layer)

**Ubicación**: `src/test/infrastructure/`

**Qué se prueba**:

- ✅ Health check del sistema
- ✅ Repositorios mock (para tests de casos de uso)

**Qué NO se prueba** (actualmente):

- ❌ Conexiones reales a base de datos
- ❌ Migraciones de BD
- ❌ Serialización/deserialización compleja

**Estrategia actual**:

- Uso de **repositorios mock** para tests rápidos y deterministas
- Los mocks simulan comportamiento de BD en memoria
- No requieren infraestructura externa

---

## 📋 Reglas Clave de Testing

### 1. Un test por comportamiento, no por método

❌ **Incorrecto**:

```python
def test_create_silo():
    # Prueba el método create

def test_save_silo():
    # Prueba el método save
```

✅ **Correcto**:

```python
def test_create_single_silo():
    # Prueba el comportamiento completo: crear Y persistir

def test_fa2_duplicate_silo_name_on_create():
    # Prueba una regla de negocio específica
```

### 2. Casos de uso: 100% de flujos cubiertos

**Flujos obligatorios por caso de uso**:

- ✅ Flujo de éxito (happy path)
- ✅ Cada regla de negocio (FA1-FA7)
- ✅ Casos borde (vacío, límites)
- ✅ Referencias rotas (IDs inexistentes)

**Cobertura actual**: 33/33 tests (100%)

### 3. No se prueban detalles internos

❌ **No probar**:

- Métodos privados (`_build_blower_from_dto`)
- Orden de llamadas internas
- Logs o prints
- Estructura de datos interna

✅ **Sí probar**:

- Comportamiento observable desde fuera
- Resultado final de operaciones
- Excepciones lanzadas
- Estado del sistema después de operación

### 4. Tests fallan solo si el negocio cambia

**Principio**: Un test debe fallar solo si:

- ✅ Una regla de negocio cambió
- ✅ Un comportamiento esperado cambió
- ✅ Un contrato público cambió

**Un test NO debe fallar si**:

- ❌ Se refactoriza código interno
- ❌ Se cambia implementación (pero no comportamiento)
- ❌ Se mejora performance sin cambiar resultado

---

## 🏗️ Estructura de Tests

### Organización por Responsabilidad

```
src/test/
├── application/
│   └── use_cases/
│       ├── test_sync_system_layout.py      # CRUD básico
│       ├── test_sync_business_rules.py     # Reglas FA3-FA7
│       └── test_get_system_layout.py       # Lectura
├── infrastructure/
│   └── test_health.py                      # Health check
└── conftest.py                             # Configuración pytest
```

### Organización por Caso de Uso

Cada archivo de test agrupa tests por **caso de uso**:

**`test_sync_system_layout.py`** (13 tests):

- Creación (4 tests)
- Actualización (2 tests)
- Eliminación (2 tests)
- Reglas FA2 (3 tests)
- Mapeo de IDs (2 tests)

**`test_sync_business_rules.py`** (14 tests):

- FA3: Jaula asignada (1 test)
- FA4: Slots duplicados (2 tests)
- FA5: Silo asignado (2 tests)
- FA6: Referencias rotas (2 tests)
- FA7: Sensores duplicados (2 tests)
- Validaciones de rangos (5 tests)

**`test_get_system_layout.py`** (6 tests):

- BD vacía (1 test)
- Con datos (3 tests)
- Consistencia (2 tests)

---

## 🧪 Anatomía de un Test

### Estructura AAA (Arrange-Act-Assert)

```python
@pytest.mark.asyncio
async def test_create_single_silo(use_case):
    # ARRANGE: Preparar datos de entrada
    request = SystemLayoutDTO(
        silos=[
            SiloConfigDTO(
                id="temp-silo-1",
                name="Silo A",
                capacity=1000.0
            )
        ],
        cages=[],
        feeding_lines=[]
    )

    # ACT: Ejecutar operación
    result = await use_case.execute(request)

    # ASSERT: Verificar resultado
    assert len(result.silos) == 1
    assert result.silos[0].name == "Silo A"
    assert result.silos[0].id != "temp-silo-1"  # ID mapeado
```

### Nomenclatura de Tests

**Patrón**: `test_<qué_se_prueba>`

**Ejemplos**:

- `test_create_single_silo` - Comportamiento básico
- `test_fa2_duplicate_silo_name_on_create` - Regla de negocio específica
- `test_get_empty_layout` - Caso borde
- `test_sync_then_get_consistency` - Integración entre casos de uso

---

## 📊 Cobertura de Reglas de Negocio

| Regla      | Descripción                 | Tests                 | Estado |
| ---------- | --------------------------- | --------------------- | ------ |
| **FA1**    | Composición mínima de línea | Implícito en creación | ✅     |
| **FA2**    | Nombres únicos              | 3 tests               | ✅     |
| **FA3**    | Jaula en una línea          | 1 test                | ✅     |
| **FA4**    | Slots únicos                | 2 tests               | ✅     |
| **FA5**    | Silo 1-a-1                  | 2 tests               | ✅     |
| **FA6**    | Referencias válidas         | 2 tests               | ✅     |
| **FA7**    | Sensores únicos por tipo    | 2 tests               | ✅     |
| **Rangos** | Validaciones numéricas      | 5 tests               | ✅     |

**Total**: 17 tests de reglas de negocio + 16 tests de operaciones = **33 tests**

---

## 🔧 Herramientas y Configuración

### Pytest

**Configuración**: `pytest.ini`

```ini
[pytest]
pythonpath = src
testpaths = src/test
asyncio_mode = auto
```

### Fixtures

**Ubicación**: `src/test/conftest.py`

**Fixtures disponibles**:

- `repositories` - Repositorios mock limpios
- `use_case` - Instancia de SyncSystemLayoutUseCase
- `get_use_case` - Instancia de GetSystemLayoutUseCase
- `sync_use_case` - Alias para sincronización

### Repositorios Mock

**Ubicación**: `src/infrastructure/persistence/mock_repositories.py`

**Características**:

- Almacenamiento en memoria (diccionarios)
- Comportamiento similar a BD real
- Estado limpio entre tests
- Validaciones básicas (ID existe, etc.)

---

## 🚀 Ejecutar Tests

### Todos los tests

```bash
python -m pytest src/test/application/use_cases/ -v
```

### Un archivo específico

```bash
python -m pytest src/test/application/use_cases/test_sync_business_rules.py -v
```

### Una clase específica

```bash
python -m pytest src/test/application/use_cases/test_sync_business_rules.py::TestFA5_SiloAlreadyAssigned -v
```

### Un test específico

```bash
python -m pytest src/test/application/use_cases/test_sync_business_rules.py::TestFA5_SiloAlreadyAssigned::test_fa5_silo_assigned_to_multiple_dosers -v
```

### Con cobertura

```bash
python -m pytest src/test/application/use_cases/ --cov=src/application --cov-report=html
```

---

## 📈 Métricas de Calidad

### Cobertura Actual

- **33 tests** implementados
- **100%** de tests pasando
- **~0.10s** tiempo de ejecución total
- **0 falsos positivos** (tests que fallan sin razón)

### Objetivos de Cobertura

- ✅ Casos de uso: 100% de flujos
- ✅ Reglas de negocio: 100% (FA1-FA7)
- ⚠️ Dominio: Cubierto indirectamente
- ⚠️ Infraestructura: Solo mocks (no BD real)

---

## 🎨 Patrones de Testing

### 1. Test de Creación

**Qué valida**: Entidad se crea y persiste correctamente

```python
async def test_create_single_silo(use_case):
    request = SystemLayoutDTO(silos=[...], cages=[], feeding_lines=[])
    result = await use_case.execute(request)

    assert len(result.silos) == 1
    assert result.silos[0].name == "Silo A"
    assert result.silos[0].id != "temp-silo-1"  # ID real
```

### 2. Test de Regla de Negocio

**Qué valida**: Regla se aplica y rechaza operación inválida

```python
async def test_fa2_duplicate_silo_name_on_create(use_case):
    # Crear primer silo
    await use_case.execute(request1)

    # Intentar crear duplicado
    with pytest.raises(Exception) as exc_info:
        await use_case.execute(request2)

    assert "Ya existe un silo con el nombre" in str(exc_info.value)
```

### 3. Test de Mapeo de IDs

**Qué valida**: IDs temporales se mapean a IDs reales

```python
async def test_id_mapping_silo_to_doser(use_case):
    request = SystemLayoutDTO(
        silos=[SiloConfigDTO(id="temp-silo-1", ...)],
        feeding_lines=[
            FeedingLineConfigDTO(
                dosers_config=[
                    DoserConfigDTO(assigned_silo_id="temp-silo-1", ...)
                ]
            )
        ]
    )

    result = await use_case.execute(request)

    doser = result.feeding_lines[0].dosers_config[0]
    silo_id = result.silos[0].id
    assert doser.assigned_silo_id == silo_id  # ID real, no temporal
```

### 4. Test de Consistencia

**Qué valida**: Múltiples operaciones mantienen consistencia

```python
async def test_sync_then_get_consistency(get_use_case, sync_use_case):
    # Sincronizar
    sync_result = await sync_use_case.execute(request)

    # Obtener
    get_result = await get_use_case.execute()

    # Deben ser idénticos
    assert len(sync_result.silos) == len(get_result.silos)
    assert sync_silo_ids == get_silo_ids
```

---

## 🔍 Debugging de Tests

### Ver output detallado

```bash
python -m pytest src/test/application/use_cases/ -v -s
```

### Ver solo fallos

```bash
python -m pytest src/test/application/use_cases/ --tb=short
```

### Ejecutar hasta primer fallo

```bash
python -m pytest src/test/application/use_cases/ -x
```

### Ver warnings

```bash
python -m pytest src/test/application/use_cases/ -v --tb=short -W default
```

---

## 📝 Buenas Prácticas

### ✅ Hacer

1. **Nombrar tests descriptivamente**: `test_fa2_duplicate_silo_name_on_create`
2. **Un assert por concepto**: Agrupar asserts relacionados
3. **Usar fixtures**: Reutilizar configuración común
4. **Probar comportamiento**: No implementación
5. **Tests independientes**: Cada test debe poder ejecutarse solo

### ❌ Evitar

1. **Tests frágiles**: Que fallen por cambios internos
2. **Tests lentos**: Usar mocks en lugar de BD real
3. **Tests acoplados**: Que dependan del orden de ejecución
4. **Magic numbers**: Usar constantes con nombres descriptivos
5. **Tests duplicados**: Consolidar tests similares

---

## 🚦 Criterios de Aceptación

Un test es **aceptable** si:

- ✅ Tiene nombre descriptivo
- ✅ Prueba un comportamiento específico
- ✅ Es independiente de otros tests
- ✅ Falla solo si el negocio cambia
- ✅ Se ejecuta en < 1 segundo

Un test debe **refactorizarse** si:

- ❌ Prueba detalles de implementación
- ❌ Depende del orden de otros tests
- ❌ Tiene lógica compleja interna
- ❌ Falla por cambios no relacionados
- ❌ Es difícil de entender

---

## 📚 Referencias

- [Cobertura de Tests](../test-coverage-summary.md)
- [Casos de Uso](../03-casos-de-uso/README.md)
- [Dominio](../02-dominio/README.md)

---

**Última actualización**: 2025-11-12  
**Total de tests**: 33  
**Cobertura**: 100% de flujos de casos de uso
