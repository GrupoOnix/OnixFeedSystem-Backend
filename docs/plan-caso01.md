Plan de Refactorización para SyncSystemLayoutUseCase (Integridad y Validación)
Este plan modifica las Tareas 1, 3 y 4 para implementar las validaciones de negocio faltantes y garantizar la atomicidad transaccional usando el patrón Unit of Work (UoW).

Tarea 1 (Modificada): Evolucionar los Agregados de Dominio
Qué: Añadir la lógica de negocio faltante a los Agregados Silo y Cage para que el Caso de Uso (Tarea 4) pueda delegarles las validaciones de asignación.

Acción:

En src/domain/aggregates/silo.py (Clase Silo):

Añadir un atributo self.\_doser_id: Optional[DoserId] = None.

Añadir un método assign_to_doser(self, doser_id: DoserId) que:

Valide la regla FA4 (1-a-1): if self.\_doser_id is not None and self.\_doser_id != doser_id: raise SiloAlreadyAssignedError(...).

Asigne self.\_doser_id = doser_id.

Añadir un método release_from_doser(self, doser_id: DoserId) que ponga self.\_doser_id = None.

En src/domain/aggregates/cage.py (Clase Cage):

Añadir un atributo self.\_status: CageStatus (un Enum con valores AVAILABLE, IN_USE).

Añadir un método assign_to_line(self) que:

Valide la regla FA3: if self.\_status == CageStatus.IN_USE: raise CageAlreadyInUseError(...).

Asigne self.\_status = CageStatus.IN_USE.

Añadir un método release_from_line(self).

Tarea 2 (Sin Cambios)
(Los DTOs en src/application/dtos.py son correctos).

Tarea 3 (Modificada): Introducir la Interfaz IUnitOfWork
Qué: Refactorizar las interfaces de repositorio para que sean gestionadas por una Unidad de Trabajo (UoW), que manejará el commit y rollback.

Acción:

En src/domain/repositories.py:

Crear una nueva interfaz IUnitOfWork(ABC).

Esta interfaz debe exponer los repositorios como propiedades:

Python

@property @abstractmethod
def lines(self) -> IFeedingLineRepository: ...

@property @abstractmethod
def silos(self) -> ISiloRepository: ...

@property @abstractstring
def cages(self) -> ICageRepository: ...
Esta interfaz debe definir los métodos de transacción:

Python

@abstractmethod
async def commit(self): ...

@abstractmethod
async def rollback(self): ...
En src/infrastructure/persistence/mock_repositories.py:

Crear class MockUnitOfWork(IUnitOfWork).

En su **init**, debe instanciar los repositorios mock:

Python

self.\_lines = MockFeedingLineRepository()
self.\_silos = MockSiloRepository()
self.\_cages = MockCageRepository()
Implementar las propiedades para devolver esas instancias (ej: @property def lines(self): return self.\_lines).

async def commit(self): pass (En el mock, el save es instantáneo).

async def rollback(self): (Aquí sí hay lógica: debe limpiar los mocks, ej: self.\_lines.clear(), self.\_silos.clear()).

Tarea 4 (Modificada): Implementar el Caso de Uso Transaccional
Qué: Reescribir SyncSystemLayoutUseCase para que use el IUnitOfWork y ejecute las validaciones faltantes (FA2, FA3, FA4).

Acción:

En src/application/use_cases/sync_system_layout.py:

Modificar **init**: El constructor ya no recibe 3 repositorios. Recibe uno:

Python

def **init**(self, uow: IUnitOfWork):
self.uow = uow
Modificar execute:

Envolver todas las Fases (1-4) en un gran bloque try...except....

Al final del bloque try (si todo tuvo éxito), llamar a await self.uow.commit().

En el bloque except (si cualquier Exception ocurre), llamar a await self.uow.rollback(), registrar el error, y luego relanzar la excepción (raise e).

Refactorizar Fases 1-4:

Reemplazar todas las llamadas a self.line_repo por self.uow.lines (ej: db_lines = await self.uow.lines.get_all()).

Reemplazar self.silo_repo por self.uow.silos.

Reemplazar self.cage_repo por self.uow.cages.

Corregir Lógica Faltante (Validaciones):

En Fase 3 (Crear Silo/Cage): Validar nombre duplicado (FA2) (ya lo tiene).

En Fase 3 (Crear Línea):

En \_resolve_silo_id, al encontrar el silo, llamar a silo.assign_to_doser(...) (FA4) y luego a await self.uow.silos.save(silo).

En assign_cage_to_slot, al encontrar la cage, llamar a cage.assign_to_line() (FA3) y luego a await self.uow.cages.save(cage).

En Fase 4 (Actualizar Silo/Cage):

Validar nombre duplicado (FA2-Update). Antes de silo.name = ..., debe verificar: existing = await self.uow.silos.find_by_name(...); if existing and existing.id != silo.id: raise Duplicate....

Implementar la actualización de silo.capacity = Weight.from_kg(dto.capacity_kg) (la corrección de diseño que notamos).

En Fase 4 (Actualizar Línea):

Repetir las validaciones de assign_to_doser (FA4) y assign_to_line (FA3) al iterar sobre las nuevas asignaciones.

(Nota: Deberá manejar la lógica de "liberar" (release) silos/jaulas que ya no están en uso).

Tarea 5 (Modificada): Actualizar el Script de Prueba
Acción:

Instanciar el MockUnitOfWork: uow_mock = MockUnitOfWork().

Instanciar el Caso de Uso: use_case = SyncSystemLayoutUseCase(uow_mock).

(El resto del script sigue igual, pero ahora verifica los repositorios dentro del mock, ej: uow_mock.lines.\_lines).
