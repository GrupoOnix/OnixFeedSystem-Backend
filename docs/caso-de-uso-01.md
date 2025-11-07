UC-01: Sincronizar Trazado del Sistema

Actor Principal
Técnico de planta (usuario con permisos de configuración)

Descripción
Permite al técnico sincronizar el estado completo de su "Canvas de Trazado" (Frontend) con la base de datos del sistema. El técnico no "crea" o "actualiza" explícitamente, sino que presiona "Guardar" para que el estado de la base de datos refleje exactamente lo que está dibujado en el canvas.

El sistema recibe el estado completo deseado, calcula las diferencias (Creaciones, Actualizaciones, Eliminaciones) y las aplica de forma transaccional.

Precondiciones
Usuario autenticado y con permisos de "Técnico".

Trigger
El técnico presiona el botón "Guardar" en la pantalla de "Trazado de Sistema".

Flujo Básico (Camino Feliz - "Sincronización de Estado")
El técnico modifica el canvas (crea, actualiza, elimina o conecta Silos, Líneas y Jaulas).

El técnico presiona "Guardar".

El Frontend recopila el estado completo del canvas y lo serializa en un DTO SaveSystemLayoutRequest.

Las entidades nuevas (dibujadas en el canvas) se envían con un id: null o un ID temporal (ej: "temp-uuid-1").

Las entidades existentes (cargadas de la BD) se envían con su id real (ej: "db-uuid-abc").

El Frontend envía el DTO SaveSystemLayoutRequest a un único endpoint transaccional (ej: PUT /api/system-layout).

El Sistema (El Caso de Uso SyncSystemLayoutUseCase) recibe el DTO.

El Sistema (Fase 1: Cálculo de Delta) carga el estado actual de la BD (IDs de todos los Silos, Jaulas y Líneas existentes).

El Sistema compara los IDs del DTO con los IDs de la BD y crea tres listas de trabajo: entidades_a_crear, entidades_a_actualizar, entidades_a_eliminar.

El Sistema (Fase 2: Eliminaciones):

Itera sobre la entidades_a_eliminar.

Llama a line_repo.delete(line_id), silo_repo.delete(silo_id), etc.

(Nota: Se valida que las entidades puedan ser eliminadas, ej: no borrar una línea mientras está alimentando).

El Sistema (Fase 3: Creaciones y Mapeo de IDs):

Crea un mapa vacío para IDs temporales: id_map = {}.

Procesa entidades_a_crear (Agregados independientes primero): a. Itera sobre los DTOs de Silo y Cage nuevos (con id temporal). b. Ensambla los VOs (SiloName, CageName, Weight.zero(), etc.). c. Crea los Agregados: new_silo = Silo(...), new_cage = Cage(...). d. Persiste: await silo_repo.save(new_silo), await cage_repo.save(new_cage). e. Mapea el ID: id_map[silo_dto.id] = new_silo.id.

Procesa entidades_a_crear (Agregados dependientes): a. Itera sobre los DTOs de FeedingLine nuevos. b. Ensambla los "hijos" (Blower, Selector). c. Ensambla los Doser(s), usando el id_map para resolver los assigned_silo_id temporales a IDs de BD reales. d. Delega (FA1): Llama a new_line = FeedingLine.create(...). e. Persiste: await line_repo.save(new_line).

El Sistema (Fase 4: Actualizaciones):

Itera sobre entidades_a_actualizar: a. Carga el Agregado existente: line = await line_repo.find_by_id(line_dto.id). b. Delega (FA4, FA3): Llama a los métodos de sincronización del Agregado (que usted creará), ej: line.sync_components(line_dto.blower, line_dto.dosers, ...). c. Delega (FA3): Llama a line.sync_assignments(line_dto.slot_assignments, cage_repo). d. Persiste: await line_repo.save(line).

(Nota: El proceso se repite para actualizar Silos y Jaulas huérfanas).

El Sistema confirma la transacción y devuelve "Éxito" al técnico.

Flujos Alternativos / Excepciones
FA1: Composición de Línea Inválida. La lógica de FeedingLine.create o line.sync_components falla (ej: sin blower). El sistema rechaza la transacción.

FA2: Nombre Duplicado. El sistema detecta que un name en un DTO nuevo ya existe en la BD (ej: line_repo.find_by_name).

FA3: Asignación de Jaula Inválida (Lógica de Dominio).

line.sync_assignments detecta que una CageId ya está asignada a otra línea (FA3 original).

line.sync_assignments detecta un slot duplicado en la misma línea (FA4 original).

FA4: Asignación de Silo Inválida (Nueva Regla 1-a-1).

Al crear o actualizar un Doser, el sistema detecta (vía silo_repo o una validación) que el SiloId asignado ya está en uso por otro Doser en el sistema. La transacción falla.

FA5: Orquestación Fallida. El DTO DoserConfigDTO hace referencia a un assigned_silo_id (temporal o real) que no existe (ni en la BD, ni en el lote de creación). La transacción falla.

Postcondiciones / Resultado
El estado de las tablas Silos, Cages, FeedingLines (y sus tablas hijas Blowers, Dosers, SlotAssignments) en la Base de Datos refleja exactamente el estado del canvas enviado por el usuario.

Todas las entidades eliminadas del canvas son eliminadas de la BD.
