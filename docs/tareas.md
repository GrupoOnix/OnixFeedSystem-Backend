Plan de Tareas para Implementar UC-01: Sincronizar Trazado del Sistema
Tarea 1: Actualizar sus Agregados de Dominio (Prerrequisito)
Qué: El Caso de Uso Sync necesita delegar la lógica de actualización a los Agregados. Sus Agregados (FeedingLine, Silo, Cage) actualmente solo tienen lógica de **init** (creación).

Acción: Debe añadir nuevos métodos a sus Agregados Raíz para manejar las actualizaciones que identificamos (Opción 2).

En FeedingLine: Añadir def sync_components(self, blower_dto, dosers_dto, ...) y def sync_assignments(self, assignments_dto).

En Silo y Cage: Añadir métodos setter para los atributos que el usuario puede cambiar (ej: silo.name = new_name).

Dónde: src/domain/aggregates/feeding_line/aggregate.py, src/domain/aggregates/silo.py, etc.

Por qué: Para que el Caso de Uso siga siendo "tonto". El Caso de Uso no debe contener ifs de lógica de negocio; debe simplemente cargar el Agregado y decirle: linea.sync_components(...).

Tarea 2: Crear los DTOs de Aplicación (El Contrato Interno)
Qué: Crear los "moldes" (dataclass puros) que definen el "estado del canvas" que su Caso de Uso recibirá.

Acción: Crear el archivo dtos.py con las clases que discutimos:

SiloConfigDTO(id: Optional[str], ...)

CageConfigDTO(id: Optional[str], ...)

BlowerConfigDTO(id: Optional[str], ...)

DoserConfigDTO(id: Optional[str], ...)

SelectorConfigDTO(id: Optional[str], ...)

SlotAssignmentDTO(...)

FeedingLineConfigDTO(id: Optional[str], blower_config: ..., dosers_config: ..., ...)

SaveSystemLayoutRequest(feeding_lines: List[...], silos: List[...], cages: List[...])

SaveSystemLayoutResponse(...)

Dónde: src/application/dtos.py

Por qué: Este es el "contrato de datos" interno y puro. Define la entrada y salida de su Caso de Uso, sin dependencias de pydantic o fastapi.

Tarea 3: Implementar los Repositorios Mock (Infraestructura)
Qué: Crear implementaciones falsas (en memoria) de sus interfaces de repositorio (IFeedingLineRepository, ISiloRepository, ICageRepository).

Acción: Crear clases que usen un dict interno para simular una base de datos.

class MockFeedingLineRepository(IFeedingLineRepository):

def **init**(self): self.\_lines = {}

async def save(self, line): self.\_lines[line.id] = line

async def find_by_id(self, id): return self.\_lines.get(id)

async def get_all_ids(self): return self.\_lines.keys()

async def delete(self, id): del self.\_lines[id]

(Repetir para MockSiloRepository y MockCageRepository).

Dónde: src/infrastructure/persistence/mock_repositories.py

Por qué: Para que el Caso de Uso pueda ser "inyectado" con estos repositorios falsos y podamos probar su lógica completa sin una base de datos real.

Tarea 4: Implementar el Caso de Uso (El Orquestador)
Qué: Escribir la clase SyncSystemLayoutUseCase que implementa el algoritmo que definimos en UC-01.

Acción:

Crear la clase SyncSystemLayoutUseCase.

Su **init** debe ser inyectado con los repositorios: def **init**(self, line_repo: IFeedingLineRepository, silo_repo: ISiloRepository, cage_repo: ICageRepository):

Implementar el método async def execute(self, request: SaveSystemLayoutRequest) -> SaveSystemLayoutResponse:.

Dentro de execute, implementar el algoritmo de 4 fases que definimos:

Fase 1: Cálculo de Delta (comparar IDs del DTO vs. IDs del Repo Mock).

Fase 2: Ejecutar Eliminaciones (llamar a repo.delete(...)).

Fase 3: Ejecutar Creaciones (llamar a Silo.create(...), FeedingLine.create(...), repo.save(...), y mapear IDs temporales).

Fase 4: Ejecutar Actualizaciones (llamar a repo.find_by_id(...), linea.sync_components(...), repo.save(...)).

Dónde: src/application/use_cases/sync_system_layout.py

Por qué: Este es el corazón de su lógica de aplicación, conectando todas las piezas.

Tarea 5: Escribir el Script de Prueba (El "Lanzador")
Qué: Crear un script de prueba (como su zmain.py) que simule el rol de FastAPI.

Acción: Este script hará lo siguiente:

Usar el truco sys.path.insert para configurar las importaciones.

Instanciar Mocks: line_repo_mock = MockFeedingLineRepository() (y los otros).

Instanciar el Caso de Uso: use_case = SyncSystemLayoutUseCase(line_repo_mock, silo_repo_mock, cage_repo_mock).

Crear un DTO de Prueba: Crear manualmente un SaveSystemLayoutRequest que simule un canvas (ej: un Silo nuevo, una FeedingLine actualizada, una Cage eliminada).

Ejecutar: await use_case.execute(dto_de_prueba).

Verificar: Imprimir el contenido de los repositorios mock (print(line_repo_mock.\_lines)) para probar que el caso de uso hizo su trabajo correctamente.

Dónde: run_sync_use_case.py (en la raíz del proyecto).

Por qué: Esto le permite probar su lógica de negocio y aplicación completa de principio a fin, antes de escribir una sola línea de código de API o base de datos.
