# Plan de Refactorización: SyncSystemLayoutUseCase

## 🎯 Objetivo

Refactorizar el caso de uso `SyncSystemLayoutUseCase` para cumplir con principios SOLID, Clean Architecture y Clean Code, mejorando legibilidad, mantenibilidad y testabilidad.

---

## 📐 Principios a aplicar

### Clean Code

- **Nombres descriptivos**: Variables, métodos y clases deben ser autoexplicativos
- **Funciones pequeñas**: Cada función debe hacer una sola cosa
- **Mínimos comentarios**: El código debe ser autoexplicativo. Solo comentar pasos clave o lógica compleja no obvia
- **Evitar duplicación**: DRY (Don't Repeat Yourself)
- **Bajo nivel de anidación**: Máximo 2-3 niveles

### SOLID

- **SRP**: Cada clase/método tiene una única responsabilidad
- **OCP**: Abierto a extensión, cerrado a modificación
- **DIP**: Depender de abstracciones, no de implementaciones

### Clean Architecture

- **Separación de capas**: Application, Domain, Infrastructure
- **Flujo de dependencias**: Hacia el dominio, nunca hacia afuera

---

## ⚠️ Restricciones importantes

### NO renombrar:

- ❌ Campos de DTOs que se mapean a modelos Pydantic
- ❌ Propiedades de entidades de dominio usadas en mappers
- ❌ Métodos públicos de interfaces de repositorios
- ❌ Nombres de value objects usados en múltiples capas

### SÍ se puede renombrar (solo si mejora la claridad):

- ✅ Variables locales dentro de métodos (solo si el nombre actual es ambiguo o poco claro)
- ✅ Métodos privados (prefijo `_`) (solo si el nombre no refleja bien su propósito)
- ✅ Parámetros de funciones internas (solo si son confusos)
- ✅ Clases de servicios nuevos (no existían antes)

**Regla**: Si un nombre ya es descriptivo y claro, NO cambiarlo. Solo renombrar cuando realmente mejore la legibilidad.

---

## 📋 Plan de Refactorización

### Fase 1: Limpieza básica (Quick wins)

#### [ ] Tarea 1.1: Eliminar comentarios TODO obsoletos

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Acción**: Buscar y eliminar todos los comentarios `# TODO` que ya están implementados

**Líneas afectadas**: ~180, ~270, ~350

**Criterio de éxito**: No quedan TODOs obsoletos en el archivo

---

#### [ ] Tarea 1.2: Simplificar docstrings excesivos

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Acción**: Reducir docstrings de métodos helper que son autoexplicativos

**Ejemplo**:

```python
# Antes (30 líneas)
def _build_sensors_from_dto(self, sensors_dto: List[SensorConfigDTO]) -> List[Sensor]:
    """
    Construye sensores desde DTOs.

    Convierte el sensor_type de string a enum SensorType.
    La validación FA7 (sensores únicos por tipo) se realiza en FeedingLine.create()
    y FeedingLine.update_components().

    Args:
        sensors_dto: Lista de DTOs de sensores

    Returns:
        Lista de entidades Sensor

    Raises:
        ValueError: Si el sensor_type no es válido
    """
    # ... código

# Después (10 líneas)
def _build_sensors_from_dto(self, sensors_dto: List[SensorConfigDTO]) -> List[Sensor]:
    """Construye sensores desde DTOs, convirtiendo sensor_type a enum."""
    # ... código
```

**Criterio de éxito**: Docstrings concisos, solo información esencial

---

#### [ ] Tarea 1.3: Reducir comentarios innecesarios

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Acción**: Eliminar comentarios que solo repiten lo que el código ya dice

**Ejemplo**:

```python
# Antes
# Mapear ID temporal -> ID real
id_map[dto.id] = new_silo.id

# Después (sin comentario, el código es claro)
id_map[dto.id] = new_silo.id
```

**Mantener solo**: Comentarios de fases principales y lógica de negocio no obvia

**Criterio de éxito**: Comentarios solo en pasos clave, código autoexplicativo

---

### Fase 2: Extraer validaciones duplicadas

#### [ ] Tarea 2.1: Crear NameValidator service

**Archivo nuevo**: `src/application/services/__init__.py`
**Archivo nuevo**: `src/application/services/name_validator.py`

**Acción**: Crear servicio para validar nombres únicos

**Contenido**:

```python
class NameValidator:
    """Valida unicidad de nombres en agregados."""

    @staticmethod
    async def validate_unique_silo_name(
        name: str,
        exclude_id: Optional[SiloId],
        repo: ISiloRepository
    ) -> None:
        """Valida que el nombre del silo sea único."""
        existing = await repo.find_by_name(SiloName(name))
        if existing and existing.id != exclude_id:
            raise DuplicateLineNameException(
                f"Ya existe un silo con el nombre '{name}'"
            )

    # Métodos similares para Cage y FeedingLine
```

**Criterio de éxito**: Validación centralizada, reutilizable

---

#### [ ] Tarea 2.2: Usar NameValidator en el caso de uso

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Acción**: Reemplazar validaciones duplicadas con llamadas al validator

**Ejemplo**:

```python
# Antes (duplicado 3 veces)
existing_silo = await self.silo_repo.find_by_name(SiloName(dto.name))
if existing_silo:
    raise DuplicateLineNameException(...)

# Después
await NameValidator.validate_unique_silo_name(
    dto.name,
    exclude_id=None,
    self.silo_repo
)
```

**Criterio de éxito**: Eliminada duplicación de validaciones

---

### Fase 3: Extraer lógica de liberación de recursos

#### [ ] Tarea 3.1: Crear ResourceReleaser service

**Archivo nuevo**: `src/application/services/resource_releaser.py`

**Acción**: Centralizar lógica de liberación de silos y jaulas

**Contenido**:

```python
class ResourceReleaser:
    """Libera recursos compartidos (silos y jaulas) de líneas de alimentación."""

    @staticmethod
    async def release_all_from_lines(
        lines: List[FeedingLine],
        silo_repo: ISiloRepository,
        cage_repo: ICageRepository
    ) -> None:
        """Libera todos los silos y jaulas de las líneas especificadas."""
        for line in lines:
            await ResourceReleaser._release_cages_from_line(line, cage_repo)
            await ResourceReleaser._release_silos_from_line(line, silo_repo)

    @staticmethod
    async def _release_cages_from_line(...):
        # Lógica de liberación de jaulas

    @staticmethod
    async def _release_silos_from_line(...):
        # Lógica de liberación de silos
```

**Criterio de éxito**: Liberación de recursos centralizada

---

#### [ ] Tarea 3.2: Usar ResourceReleaser en Fase 4.3a

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Acción**: Reemplazar loops de liberación con llamada al service

**Ejemplo**:

```python
# Antes (30+ líneas)
for line_id, dto in lines_to_update_dto_map.items():
    line = await self.line_repo.find_by_id(line_id)
    for old_assignment in line.get_slot_assignments():
        # ... liberación manual

# Después (3 líneas)
lines_to_release = [await self.line_repo.find_by_id(lid)
                    for lid in lines_to_update_dto_map.keys()]
await ResourceReleaser.release_all_from_lines(
    lines_to_release, self.silo_repo, self.cage_repo
)
```

**Criterio de éxito**: Fase 4.3a reducida significativamente

---

### Fase 4: Extraer cálculo de delta

#### [ ] Tarea 4.1: Crear clase Delta (DTO interno)

**Archivo nuevo**: `src/application/services/delta_calculator.py`

**Acción**: Crear estructura de datos para representar el delta

**Contenido**:

```python
@dataclass
class Delta:
    """Representa las diferencias entre el estado deseado y el actual."""
    silos_to_create: List[SiloConfigDTO]
    silos_to_update: Dict[SiloId, SiloConfigDTO]
    silos_to_delete: Set[SiloId]

    cages_to_create: List[CageConfigDTO]
    cages_to_update: Dict[CageId, CageConfigDTO]
    cages_to_delete: Set[CageId]

    lines_to_create: List[FeedingLineConfigDTO]
    lines_to_update: Dict[LineId, FeedingLineConfigDTO]
    lines_to_delete: Set[LineId]
```

**Criterio de éxito**: Estructura clara para representar cambios

---

#### [ ] Tarea 4.2: Crear DeltaCalculator service

**Archivo**: `src/application/services/delta_calculator.py`

**Acción**: Extraer lógica de cálculo de delta (Fase 1)

**Contenido**:

```python
class DeltaCalculator:
    """Calcula diferencias entre estado deseado y actual."""

    @staticmethod
    async def calculate(
        request: SystemLayoutDTO,
        line_repo: IFeedingLineRepository,
        silo_repo: ISiloRepository,
        cage_repo: ICageRepository
    ) -> Delta:
        """Calcula qué crear, actualizar y eliminar."""
        # Lógica de Fase 1 movida aquí
        return Delta(...)
```

**Criterio de éxito**: Fase 1 extraída a servicio dedicado

---

#### [ ] Tarea 4.3: Usar DeltaCalculator en execute()

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Acción**: Reemplazar Fase 1 con llamada al calculator

**Ejemplo**:

```python
# Antes (80+ líneas)
db_lines = await self.line_repo.get_all()
# ... cálculo manual de delta

# Después (3 líneas)
delta = await DeltaCalculator.calculate(
    request, self.line_repo, self.silo_repo, self.cage_repo
)
```

**Criterio de éxito**: Método execute() más corto y legible

---

### Fase 5: Extraer fases a métodos privados

#### [ ] Tarea 5.1: Extraer Fase 2 (Eliminaciones)

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Acción**: Crear método `_execute_deletions(delta: Delta)`

**Contenido**:

```python
async def _execute_deletions(self, delta: Delta) -> None:
    """Elimina agregados que no están en el request."""
    for line_id in delta.lines_to_delete:
        await self.line_repo.delete(line_id)

    for silo_id in delta.silos_to_delete:
        await self.silo_repo.delete(silo_id)

    for cage_id in delta.cages_to_delete:
        await self.cage_repo.delete(cage_id)
```

**Criterio de éxito**: Fase 2 en método dedicado

---

#### [ ] Tarea 5.2: Extraer Fase 3 (Creaciones)

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Acción**: Crear método `_execute_creations(delta: Delta, id_map: Dict) -> None`

**Contenido**:

```python
async def _execute_creations(self, delta: Delta, id_map: Dict[str, Any]) -> None:
    """Crea nuevos agregados y mapea IDs temporales a reales."""
    await self._create_silos(delta.silos_to_create, id_map)
    await self._create_cages(delta.cages_to_create, id_map)
    await self._create_feeding_lines(delta.lines_to_create, id_map)
```

**Sub-métodos**:

- `_create_silos()`
- `_create_cages()`
- `_create_feeding_lines()`

**Criterio de éxito**: Fase 3 dividida en métodos pequeños

---

#### [ ] Tarea 5.3: Extraer Fase 4 (Actualizaciones)

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Acción**: Crear método `_execute_updates(delta: Delta, id_map: Dict) -> None`

**Contenido**:

```python
async def _execute_updates(self, delta: Delta, id_map: Dict[str, Any]) -> None:
    """Actualiza agregados existentes."""
    await self._update_silos(delta.silos_to_update)
    await self._update_cages(delta.cages_to_update)
    await self._update_feeding_lines(delta.lines_to_update, id_map)
```

**Sub-métodos**:

- `_update_silos()`
- `_update_cages()`
- `_update_feeding_lines()` (incluye Fase 4.3a y 4.3b)

**Criterio de éxito**: Fase 4 dividida en métodos pequeños

---

#### [ ] Tarea 5.4: Extraer Fase 5 (Reconstrucción)

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Acción**: Crear método `_rebuild_layout(presentation_data: Dict) -> SystemLayoutDTO`

**Contenido**:

```python
async def _rebuild_layout(self, presentation_data: Dict[str, Any]) -> SystemLayoutDTO:
    """Reconstruye el layout completo con IDs reales desde BD."""
    all_silos = await self.silo_repo.get_all()
    all_cages = await self.cage_repo.get_all()
    all_lines = await self.line_repo.get_all()

    return SystemLayoutDTO(
        silos=[DomainToDTOMapper.silo_to_dto(s) for s in all_silos],
        cages=[DomainToDTOMapper.cage_to_dto(c) for c in all_cages],
        feeding_lines=[DomainToDTOMapper.feeding_line_to_dto(l) for l in all_lines],
        presentation_data=presentation_data
    )
```

**Criterio de éxito**: Fase 5 en método dedicado

---

#### [ ] Tarea 5.5: Refactorizar execute() principal

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Acción**: Simplificar método principal usando métodos extraídos

**Resultado esperado**:

```python
async def execute(self, request: SystemLayoutDTO) -> SystemLayoutDTO:
    """Sincroniza el layout del sistema aplicando cambios de forma transaccional."""
    id_map: Dict[str, Any] = {}

    delta = await DeltaCalculator.calculate(
        request, self.line_repo, self.silo_repo, self.cage_repo
    )

    await self._execute_deletions(delta)
    await self._execute_creations(delta, id_map)
    await self._execute_updates(delta, id_map)

    return await self._rebuild_layout(request.presentation_data)
```

**Criterio de éxito**: Método execute() de ~15 líneas, altamente legible

---

### Fase 6: Optimizaciones finales

#### [ ] Tarea 6.1: Revisar nombres de variables locales

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Acción**: Mejorar nombres de variables internas **solo si son ambiguos o confusos** (no forzar cambios innecesarios)

**Ejemplos de cuándo SÍ renombrar**:

- `dto` → `silo_dto` (solo si hay múltiples DTOs en el mismo contexto y no es obvio cuál es)
- `line` → `existing_line` (solo si hay confusión entre línea nueva vs existente)
- Variables de un solo carácter → nombres descriptivos (solo si no es obvio qué representan)

**Ejemplos de cuándo NO renombrar**:

- `dto` está bien si el contexto es claro (ej: dentro de `_create_silo(dto)`)
- `line` está bien si solo hay una línea en el scope
- `i`, `j` están bien en loops simples

**Criterio de éxito**: Variables autoexplicativas, sin cambios innecesarios

---

#### [ ] Tarea 6.2: Reducir nivel de anidación

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Acción**: Usar early returns y guard clauses

**Ejemplo**:

```python
# Antes (3 niveles)
for line_id, dto in lines_to_update_dto_map.items():
    line = await self.line_repo.find_by_id(line_id)
    if not line:
        continue
    # ... lógica

# Después (2 niveles)
for line_id, dto in lines_to_update_dto_map.items():
    line = await self.line_repo.find_by_id(line_id)
    if not line:
        continue

    await self._update_single_line(line, dto, id_map)
```

**Criterio de éxito**: Máximo 2-3 niveles de anidación

---

#### [ ] Tarea 6.3: Actualizar imports

**Archivo**: `src/application/use_cases/sync_system_layout.py`

**Acción**: Agregar imports de servicios nuevos

**Agregar**:

```python
from application.services import (
    DeltaCalculator,
    NameValidator,
    ResourceReleaser
)
```

**Criterio de éxito**: Imports organizados y completos

---

#### [ ] Tarea 6.4: Ejecutar tests

**Archivo**: `src/test/test_sync_system_layout_use_case.py`

**Acción**: Verificar que todos los tests existentes siguen pasando

**Comando**: `pytest src/test/test_sync_system_layout_use_case.py -v`

**Criterio de éxito**: Todos los tests pasan (17/17)

---

#### [ ] Tarea 6.5: Verificar integración con API

**Acción**: Probar endpoint completo con JSON real

**Comando**: `curl -X POST http://localhost:8000/api/system-layout -d @model_option_a.json`

**Criterio de éxito**: Endpoint funciona correctamente, respuesta con IDs reales

---

## 📊 Métricas de éxito

### Antes de refactorización:

- Líneas en `execute()`: ~300
- Complejidad ciclomática: ~25
- Nivel de anidación: 4-5
- Código duplicado: 3 instancias de validación
- Comentarios: ~50 líneas

### Después de refactorización:

- Líneas en `execute()`: ~15
- Complejidad ciclomática: ~5
- Nivel de anidación: 2-3
- Código duplicado: 0
- Comentarios: ~10 líneas (solo esenciales)

---

## 🎯 Resultado esperado

Un caso de uso que:

- ✅ Es fácil de leer y entender
- ✅ Cumple con SRP (cada método hace una cosa)
- ✅ No tiene duplicación (DRY)
- ✅ Tiene bajo acoplamiento
- ✅ Es fácil de testear
- ✅ Tiene mínimos comentarios (código autoexplicativo)
- ✅ Mantiene compatibilidad con otras capas

---

## 📝 Notas finales

- Hacer commit después de cada fase completada
- Ejecutar tests después de cada tarea crítica
- No renombrar nada que rompa mappers o DTOs
- Mantener la lógica de negocio intacta
- Priorizar legibilidad sobre brevedad
