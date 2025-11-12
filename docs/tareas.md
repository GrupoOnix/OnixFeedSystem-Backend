Plan de Tareas Actualizado para UC-01: Sincronizar Trazado del Sistema

Tarea 1: Evolucionar los Agregados de Dominio (Prerrequisito)
Qué: Adaptar sus Agregados Raíz (FeedingLine, Silo, Cage) para que soporten la lógica de "sincronización" (actualización y validación de secuencia) que requiere el UC-01.

Acción:

En FeedingLine:

Modificar FeedingLine.create para que acepte relations_data: dict. Su lógica de validación interna ahora debe usar esto para verificar la secuencia (FA2: Doser antes de Blower).

Añadir el @name.setter para self.\_name.

Añadir def update_components(self, blower: IBlower, dosers: List[IDoser], selector: ISelector, ..., relations_data: dict): Este método debe re-validar la composición mínima (FA1) y la secuencia (FA2) usando los nuevos componentes y las nuevas relaciones.

Añadir def update_assignments(self, new_assignments: List[SlotAssignment]): Este método debe limpiar y reaplicar las asignaciones, validando duplicados (FA4) y la capacidad del selector.

En Silo y Cage:

Añadir los setters necesarios para los atributos que se pueden modificar desde el canvas (ej: @name.setter en Silo, @name.setter en Cage).

Dónde: src/domain/aggregates/

Por qué: Para que el Caso de Uso delegue toda la lógica de negocio (FA1, FA2, FA4) a los Agregados.

Tarea 2: Crear los DTOs de Aplicación (El Contrato del Canvas)
Qué: Definir los dataclass puros que representan el DTO SaveSystemLayoutRequest completo.

Acción: Crear (o actualizar) el archivo dtos.py con:

SiloConfigDTO(id: Optional[str], ...)

CageConfigDTO(id: Optional[str], ...)

BlowerConfigDTO(id: Optional[str], ...)

DoserConfigDTO(id: Optional[str], ...)

SelectorConfigDTO(id: Optional[str], ...)

SlotAssignmentDTO(...)

FeedingLineConfigDTO(id: Optional[str], blower_config: ..., dosers_config: ..., ...)

SaveSystemLayoutRequest: Esta es la clase principal. Debe contener:

silos: List[SiloConfigDTO]

cages: List[CageConfigDTO]

feeding_lines: List[FeedingLineConfigDTO]

relations_data: dict

presentation_data: dict

SaveSystemLayoutResponse(status: str, ...)

Dónde: src/application/dtos.py

Por qué: Este es el "formulario" completo que su frontend enviará y que su Caso de Uso recibirá.

Tarea 3: Implementar los Repositorios Mock (Infraestructura)
Qué: Crear implementaciones falsas (en memoria) de sus interfaces de repositorio existentes (IFeedingLineRepository, ISiloRepository, ICageRepository).

Acción:

Crear un nuevo archivo en src/infrastructure/persistence/mock_repositories.py.

Dentro de ese archivo, implementar las clases MockFeedingLineRepository, MockSiloRepository, y MockCageRepository.

Cada clase mock debe implementar todos los métodos de su interfaz correspondiente (ej: save, find_by_id, find_by_name, get_all, y get_next_id).

Usará un dict en memoria (ej: self.\_lines = {}) para simular la base de datos (guardando en save, leyendo en find_by_id, etc.).

Dónde: src/infrastructure/persistence/mock_repositories.py

Por qué: Para que el Caso de Uso (Tarea 4) pueda ser "inyectado" con estos repositorios falsos y podamos probar su lógica completa sin una base de datos real.

Saludos. Su corrección es 100% precisa y bienvenida. Mi plan de tareas anterior se basaba en suposiciones que usted ha invalidado con el código que ha proporcionado.

Como su arquitecto de software, me alinearé con su diseño:

Interfaces Definidas: Tiene razón, las interfaces IFeedingLineRepository, ICageRepository, y ISiloRepository ya están definidas. La "Tarea 3" no debe "definirlas", sino implementarlas.

Ruta de Archivo: Tiene razón, su archivo está en domain/repositories.py. Usaremos esa ruta (mi sugerencia de domain/shared/repositories.py queda descartada).

Alcance (Scope): Tiene razón, ha decidido posponer el ILayoutRepository. Esta es una decisión de ingeniería excelente para reducir el alcance inicial. Nos enfocaremos solo en los 3 repositorios de Agregados.

Plan de Tareas Actualizado (Tareas 3, 4 y 5)
Aquí está el plan de tareas actualizado, comenzando con su Tarea 3 corregida. He eliminado el ILayoutRepository de todas las tareas posteriores (4 y 5) para reflejar este nuevo alcance.

Tarea 3: Implementar los Repositorios Mock (Infraestructura)
Qué: Crear implementaciones falsas (en memoria) de sus interfaces de repositorio existentes (IFeedingLineRepository, ISiloRepository, ICageRepository).

Acción:

Crear un nuevo archivo en src/infrastructure/persistence/mock_repositories.py.

Dentro de ese archivo, implementar las clases MockFeedingLineRepository, MockSiloRepository, y MockCageRepository.

Cada clase mock debe implementar todos los métodos de su interfaz correspondiente (ej: save, find_by_id, find_by_name, get_all, y get_next_id).

Usará un dict en memoria (ej: self.\_lines = {}) para simular la base de datos (guardando en save, leyendo en find_by_id, etc.).

Dónde: src/infrastructure/persistence/mock_repositories.py

Por qué: Para que el Caso de Uso (Tarea 4) pueda ser "inyectado" con estos repositorios falsos y podamos probar su lógica completa sin una base de datos real.

Tarea 4: Implementar el Caso de Uso SyncSystemLayoutUseCase (El Orquestador)

Qué: Escribir la clase SyncSystemLayoutUseCase que implementa el algoritmo UC-01.

Acción:

Crear la clase SyncSystemLayoutUseCase.

Su **init** debe ser inyectado con los repositorios: def **init**(self, line_repo: IFeedingLineRepository, silo_repo: ISiloRepository, cage_repo: ICageRepository):

Implementar async def execute(self, request: SaveSystemLayoutRequest) -> SaveSystemLayoutResponse:.

Dentro de execute, implementar el algoritmo del UC-01 (Fases 1-4).

Eliminar la "Fase 5 (Metadatos)" del algoritmo, ya que ILayoutRepository está fuera de alcance.

Dónde: src/application/use_cases/sync_system_layout.py

Por qué: Este es el corazón de la aplicación, implementando el flujo completo de la transacción de negocio (excluyendo los metadatos de presentación por ahora).

Tarea 5: Escribir el Script de Prueba (El "Lanzador")
Qué: Crear un run_sync_use_case.py que pruebe el Caso de Uso (sin ILayoutRepository).

Acción:

Usar sys.path.insert.

Instanciar Mocks: line_repo_mock = MockFeedingLineRepository(), silo_repo_mock = MockSiloRepository(), cage_repo_mock = MockCageRepository().

Instanciar el Caso de Uso: use_case = SyncSystemLayoutUseCase(line_repo_mock, silo_repo_mock, cage_repo_mock).

Crear un DTO de Prueba SaveSystemLayoutRequest (sin relations_data ni presentation_data por ahora, ya que no se usarán en la Tarea 4).

Ejecutar: await use_case.execute(dto_de_prueba).

Verificar: Imprimir el contenido de los repositorios mock (print(line_repo_mock.\_lines)) para probar que el "diff" (crear, actualizar, eliminar) funcionó.

Dónde: run_sync_use_case.py (en la raíz del proyecto).

Por qué: Para tener confianza total en su lógica de sincronización de Agregados.
