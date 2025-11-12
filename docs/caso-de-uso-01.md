UC-01: Sincronizar Trazado del Sistema

Actor Principal
Técnico de planta (usuario con permisos de configuración)

Descripción
Permite al técnico sincronizar el estado completo de su "Canvas de Trazado" (Frontend) con la base de datos del sistema. El técnico no "crea" o "actualiza" explícitamente, sino que presiona "Guardar" para que el estado de la base de datos refleje exactamente lo que está dibujado en el canvas.

El sistema recibe el estado completo deseado (DTO), que incluye Líneas, Silos, Jaulas, Relaciones y Datos de Presentación. El sistema calcula las diferencias (Creaciones, Actualizaciones, Eliminaciones) y las aplica de forma transaccional.

Precondiciones
Usuario autenticado y con permisos de "Técnico".

Trigger
El técnico presiona el botón "Guardar" en la pantalla de "Trazado de Sistema".

Flujo Básico (Camino Feliz - "Sincronización de Estado")
El técnico modifica el canvas (crea, actualiza, elimina o conecta Silos, Líneas y Jaulas).

El técnico presiona "Guardar".

El Frontend recopila el estado completo del canvas y lo serializa en un DTO SaveSystemLayoutRequest. Este DTO contiene:

silos: List[SiloConfigDTO]

cages: List[CageConfigDTO]

feeding_lines: List[FeedingLineConfigDTO]

relations_data: dict (Datos de conexión, ej: [{ "from": "blower-1", "to": "doser-1" }])

presentation_data: dict (Datos de UI, ej: {"blower-1": {"x": 10, "y": 20}})

(Nota: Las entidades nuevas se envían con un id temporal; las existentes con su id real de BD).

El Frontend envía el DTO SaveSystemLayoutRequest a un único endpoint transaccional (ej: PUT /api/system-layout).

El Sistema (Caso de Uso SyncSystemLayoutUseCase) recibe el DTO.

El Sistema (Fase 1: Cálculo de Delta) carga los IDs de todos los Agregados (Silos, Cages, FeedingLines) existentes en la BD.

El Sistema compara los IDs del DTO con los IDs de la BD y crea tres conjuntos de trabajo: ids_a_crear, ids_a_actualizar, ids_a_eliminar.

El Sistema (Fase 2: Eliminaciones Implícitas):

Itera sobre ids_a_eliminar.

Llama a line_repo.delete(line_id), silo_repo.delete(silo_id), etc. (Validando reglas de negocio, ej: no borrar si está en uso).

El Sistema (Fase 3: Creaciones y Mapeo de IDs):

Crea un mapa vacío para IDs temporales: id_map = {}.

Procesa ids_a_crear (Agregados independientes primero): a. Itera sobre los DTOs de Silo y Cage nuevos (con id temporal). b. Ensambla los VOs y crea los Agregados new_silo = Silo(...), new_cage = Cage(...). c. Persiste: await silo_repo.save(new_silo), await cage_repo.save(new_cage). d. Mapea el ID: id_map[silo_dto.id_temporal] = new_silo.id_real_db.

Procesa ids_a_crear (Agregados dependientes): a. Itera sobre los DTOs de FeedingLine nuevos. b. Ensambla los "hijos" (Blower, Selector). c. Ensambla los Doser(s), usando el id_map para resolver los assigned_silo_id temporales a IDs de BD reales. d. Delega (FA1): Llama a new_line = FeedingLine.create(...). e. Persiste: await line_repo.save(new_line).

El Sistema (Fase 4: Actualizaciones):

Itera sobre ids_a_actualizar: a. Carga el Agregado existente: line = await line_repo.find_by_id(line_dto.id). b. Delega (FA4, FA3): Llama a los métodos de sincronización del Agregado (ej: line.sync_components(...), line.sync_assignments(...)). c. Persiste: await line_repo.save(line).

(El proceso se repite para actualizar Silos y Jaulas huérfanas).

El Sistema (Fase 5: Persistencia de Metadatos):

Guarda los datos de presentation_data y relations_data en un formato adecuado (ej: una tabla de "Layout" o columnas JSON), ya que estos no afectan al Dominio.

El Sistema confirma la transacción y devuelve "Éxito" al técnico.

Flujos Alternativos / Excepciones
FA1: Composición de Línea Inválida. La lógica de FeedingLine.create o line.sync_components falla (ej: sin blower). El sistema rechaza la transacción.

FA2: Trazado en orden incorrecto. (Validación movida al Dominio). El método FeedingLine.create (o sync_components) recibe los relations_data. Si la secuencia es ilógica (Doser antes de Blower), el Agregado FeedingLine lanza una InvalidSequenceException.

FA3: Nombre Duplicado. El sistema detecta que un name en un DTO nuevo (Silo, Cage o Línea) ya existe en la BD.

FA4: Asignación de Jaula Inválida (Lógica de Dominio).

line.sync_assignments (delegado al Agregado) detecta que una CageId ya está asignada a otra línea.

line.sync_assignments detecta un slot duplicado en la misma línea.

FA5: Asignación de Silo Inválida (Regla 1-a-1).

Al sincronizar un Doser, el sistema detecta (vía silo_repo o una validación) que el SiloId asignado ya está en uso por otro Doser en el sistema. La transacción falla.

FA6: Orquestación Fallida (ID Roto). El DTO DoserConfigDTO hace referencia a un assigned_silo_id (o un SlotAssignment a un cage_id) que no existe (ni en la BD, ni en el lote de creación id_map). La transacción falla.

FA7: Sensores Duplicados por Tipo. Al sincronizar los componentes de una línea, el sistema detecta que hay más de un sensor del mismo tipo (ej: dos sensores de TEMPERATURE). Los sensores son opcionales, pero solo puede haber uno de cada tipo por línea. La transacción falla.

Postcondiciones / Resultado
El estado de los Agregados (Silos, Cages, FeedingLines) en la BD refleja exactamente el estado de negocio dibujado en el canvas.

Los metadatos de presentation_data y relations_data se guardan para poder redibujar el canvas.

Todas las entidades eliminadas del canvas son eliminadas de la BD.
