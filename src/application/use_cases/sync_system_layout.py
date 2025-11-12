import uuid
from typing import Dict, List, Any, Optional

from application.dtos import (
    SystemLayoutDTO,
    SiloConfigDTO,
    CageConfigDTO,
    FeedingLineConfigDTO,
    BlowerConfigDTO,
    SensorConfigDTO,
    DoserConfigDTO,
    SelectorConfigDTO,
    SlotAssignmentDTO
)
from application.mappers import DomainToDTOMapper
from domain.repositories import (
    IFeedingLineRepository,
    ISiloRepository,
    ICageRepository
)
from domain.aggregates.silo import Silo
from domain.aggregates.cage import Cage
from domain.aggregates.feeding_line.feeding_line import FeedingLine
from domain.aggregates.feeding_line.blower import Blower
from domain.aggregates.feeding_line.doser import Doser
from domain.aggregates.feeding_line.selector import Selector
from domain.aggregates.feeding_line.sensor import Sensor
from domain.value_objects import (
    LineId, LineName,
    SiloId, SiloName, Weight,
    CageId, CageName,
    BlowerName, BlowerPowerPercentage, BlowDurationInSeconds,
    DoserName, DosingRange, DosingRate,
    SelectorName, SelectorCapacity, SelectorSpeedProfile,
    SensorName,
    SlotNumber, SlotAssignment
)
from domain.exceptions import DuplicateLineNameException
from domain.enums import SensorType


class SyncSystemLayoutUseCase:

    def __init__(self,
                 line_repo: IFeedingLineRepository,
                 silo_repo: ISiloRepository,
                 cage_repo: ICageRepository):

        self.line_repo = line_repo
        self.silo_repo = silo_repo
        self.cage_repo = cage_repo

    async def execute(self, request: SystemLayoutDTO) -> SystemLayoutDTO:
       
        id_map: Dict[str, Any] = {}
        
        # ====================================================================
        # FASE 1: CÁLCULO DE DELTA
        # ====================================================================
        
        # 1.1 Cargar todos los IDs reales de la BD
        db_lines = await self.line_repo.get_all()
        db_silos = await self.silo_repo.get_all()
        db_cages = await self.cage_repo.get_all()
        
        db_line_ids_set = {line.id for line in db_lines}
        db_silo_ids_set = {silo.id for silo in db_silos}
        db_cage_ids_set = {cage.id for cage in db_cages}
        
        # 1.2 Separar DTOs en "Crear" vs "Actualizar"
        
        silos_to_update_dto_map: Dict[SiloId, SiloConfigDTO] = {}
        silos_to_create_dtos: List[SiloConfigDTO] = []
        
        for dto in request.silos:
            if self._is_uuid(dto.id):
                silo_id = SiloId.from_string(dto.id)
                silos_to_update_dto_map[silo_id] = dto
            else:
                silos_to_create_dtos.append(dto)
        
        cages_to_update_dto_map: Dict[CageId, CageConfigDTO] = {}
        cages_to_create_dtos: List[CageConfigDTO] = []
        
        for dto in request.cages:
            if self._is_uuid(dto.id):
                cage_id = CageId.from_string(dto.id)
                cages_to_update_dto_map[cage_id] = dto
            else:
                cages_to_create_dtos.append(dto)
        
        lines_to_update_dto_map: Dict[LineId, FeedingLineConfigDTO] = {}
        lines_to_create_dtos: List[FeedingLineConfigDTO] = []
        
        for dto in request.feeding_lines:
            if self._is_uuid(dto.id):
                line_id = LineId.from_string(dto.id)
                lines_to_update_dto_map[line_id] = dto
            else:
                lines_to_create_dtos.append(dto)
        
        # 1.3 Calcular IDs a eliminar
        silo_ids_to_delete = db_silo_ids_set - set(silos_to_update_dto_map.keys())
        cage_ids_to_delete = db_cage_ids_set - set(cages_to_update_dto_map.keys())
        line_ids_to_delete = db_line_ids_set - set(lines_to_update_dto_map.keys())
        
        # ====================================================================
        # FASE 2: EJECUTAR ELIMINACIONES
        # ====================================================================
        
        for line_id in line_ids_to_delete:
            await self.line_repo.delete(line_id)
        
        for silo_id in silo_ids_to_delete:
            await self.silo_repo.delete(silo_id)
        
        for cage_id in cage_ids_to_delete:
            await self.cage_repo.delete(cage_id)
        
        # ====================================================================
        # FASE 3: EJECUTAR CREACIONES (y Mapear IDs)
        # ====================================================================
        
        # 3.1 Crear Agregados Independientes: Silos
        for dto in silos_to_create_dtos:
            existing_silo = await self.silo_repo.find_by_name(SiloName(dto.name))
            if existing_silo:
                raise DuplicateLineNameException(
                    f"Ya existe un silo con el nombre '{dto.name}'"
                )
            
            name = SiloName(dto.name)
            capacity = Weight.from_kg(dto.capacity)
            stock_level = Weight.zero()
            
            new_silo = Silo(name=name, capacity=capacity, stock_level=stock_level)
            
            await self.silo_repo.save(new_silo)
            
            # Mapear ID temporal -> ID real
            id_map[dto.id] = new_silo.id
        
        # 3.2 Crear Agregados Independientes: Cages
        for dto in cages_to_create_dtos:
            existing_cage = await self.cage_repo.find_by_name(CageName(dto.name))
            if existing_cage:
                raise DuplicateLineNameException(
                    f"Ya existe una jaula con el nombre '{dto.name}'"
                )
            
            name = CageName(dto.name)
            
            new_cage = Cage(name=name)
            
            await self.cage_repo.save(new_cage)
            
            id_map[dto.id] = new_cage.id

        # 3.3 Crear Agregados Dependientes: FeedingLines
        for dto in lines_to_create_dtos:
            existing_line = await self.line_repo.find_by_name(LineName(dto.line_name))
            if existing_line:
                raise DuplicateLineNameException(
                    f"Ya existe una línea con el nombre '{dto.line_name}'"
                )
            
            blower = self._build_blower_from_dto(dto.blower_config)
            sensors = self._build_sensors_from_dto(dto.sensors_config)
            dosers = await self._build_dosers_from_dto(dto.dosers_config, id_map)
            selector = self._build_selector_from_dto(dto.selector_config)
            
            new_line = FeedingLine.create(
                name=LineName(dto.line_name),
                blower=blower,
                dosers=dosers,
                selector=selector,
                sensors=sensors
            )
            
            # Validar y asignar slots (Jaula no debe estar en uso por otra línea)
            for slot_dto in dto.slot_assignments:
                cage_id = await self._resolve_cage_id(slot_dto.cage_id, id_map)
                
                # Validar que la jaula no esté asignada a otra línea
                cage = await self.cage_repo.find_by_id(cage_id)
                if cage:
                    cage.assign_to_line()  # Lanza excepción si ya está en uso
                    await self.cage_repo.save(cage)  # Persistir cambio de estado
                
                new_line.assign_cage_to_slot(slot_dto.slot_number, cage_id)
            
            # Mapear ID temporal de la línea -> ID real
            id_map[dto.id] = new_line.id
            
            # Mapear IDs temporales de componentes -> IDs reales
            id_map[dto.blower_config.id] = new_line.blower.id
            id_map[dto.selector_config.id] = new_line.selector.id
            
            for i, sensor in enumerate(new_line.sensors):
                id_map[dto.sensors_config[i].id] = sensor.id
            
            for i, doser in enumerate(new_line.dosers):
                id_map[dto.dosers_config[i].id] = doser.id
            
            # Guardar presentation_metadata de esta línea (si existe)
            line_presentation = request.presentation_data.get("lines", {}).get(dto.id, None)
            if line_presentation:
                updated_presentation = self._replace_temp_ids_in_presentation(
                    line_presentation, id_map
                )
                new_line.set_presentation_metadata(updated_presentation)
            
            await self.line_repo.save(new_line)
        
        # ====================================================================
        # FASE 4: EJECUTAR ACTUALIZACIONES
        # ====================================================================
        
        # 4.1 Actualizar Agregados Independientes: Silos
        for silo_id, dto in silos_to_update_dto_map.items():
            silo = await self.silo_repo.find_by_id(silo_id)
            if not silo:
                continue  # Skip si no existe
            
            # Validar FA2: Nombre duplicado (solo si cambió el nombre)
            if str(silo.name) != dto.name:
                existing_silo = await self.silo_repo.find_by_name(SiloName(dto.name))
                if existing_silo and existing_silo.id != silo_id:
                    raise DuplicateLineNameException(
                        f"Ya existe un silo con el nombre '{dto.name}'"
                    )
                silo.name = SiloName(dto.name)
            
            # Actualizar capacidad (valida automáticamente vs stock_level en el setter)
            silo.capacity = Weight.from_kg(dto.capacity)
            
            await self.silo_repo.save(silo)
        
        # 4.2 Actualizar Agregados Independientes: Cages
        for cage_id, dto in cages_to_update_dto_map.items():
            cage = await self.cage_repo.find_by_id(cage_id)
            if not cage:
                continue  # Skip si no existe
            
            # Validar FA2: Nombre duplicado (solo si cambió el nombre)
            if str(cage.name) != dto.name:
                existing_cage = await self.cage_repo.find_by_name(CageName(dto.name))
                if existing_cage and existing_cage.id != cage_id:
                    raise DuplicateLineNameException(
                        f"Ya existe una jaula con el nombre '{dto.name}'"
                    )
                cage.name = CageName(dto.name)
            
            await self.cage_repo.save(cage)
        
        # 4.3 Actualizar Agregados Dependientes: FeedingLines
        # Patrón "Release All → Assign All" para evitar conflictos en intercambios
        
        # ====================================================================
        # FASE 4.3a: LIBERAR TODOS LOS RECURSOS COMPARTIDOS
        # ====================================================================
        # Liberar TODAS las jaulas y silos de TODAS las líneas antes de reasignar
        # Esto permite intercambios entre líneas (ej: Line1→Silo1, Line2→Silo2 
        # puede cambiar a Line1→Silo2, Line2→Silo1)
        
        for line_id, dto in lines_to_update_dto_map.items():
            line = await self.line_repo.find_by_id(line_id)
            if not line:
                continue
            
            # Liberar jaulas antiguas
            old_assignments = line.get_slot_assignments()
            for old_assignment in old_assignments:
                old_cage = await self.cage_repo.find_by_id(old_assignment.cage_id)
                if old_cage:
                    old_cage.release_from_line()
                    await self.cage_repo.save(old_cage)
            
            # Liberar silos antiguos
            for old_doser in line.dosers:
                old_silo = await self.silo_repo.find_by_id(old_doser.assigned_silo_id)
                if old_silo:
                    old_silo.release_from_doser()
                    await self.silo_repo.save(old_silo)
        
        # ====================================================================
        # FASE 4.3b: REASIGNAR TODOS LOS RECURSOS
        # ====================================================================
        # Ahora que todos los recursos están libres, podemos reasignarlos
        
        for line_id, dto in lines_to_update_dto_map.items():
            line = await self.line_repo.find_by_id(line_id)
            if not line:
                continue
            
            # Validar nombre duplicado (solo si cambió el nombre)
            if str(line.name) != dto.line_name:
                existing_line = await self.line_repo.find_by_name(LineName(dto.line_name))
                if existing_line and existing_line.id != line_id:
                    raise DuplicateLineNameException(
                        f"Ya existe una línea con el nombre '{dto.line_name}'"
                    )
                line.name = LineName(dto.line_name)
            
            # Construir componentes (asigna silos internamente)
            blower = self._build_blower_from_dto(dto.blower_config)
            sensors = self._build_sensors_from_dto(dto.sensors_config)
            dosers = await self._build_dosers_from_dto(dto.dosers_config, id_map)
            selector = self._build_selector_from_dto(dto.selector_config)
            
            line.update_components(blower, dosers, selector, sensors)
            
            # Ensamblar y asignar jaulas
            new_assignments: List[SlotAssignment] = []
            for slot_dto in dto.slot_assignments:
                cage_id = await self._resolve_cage_id(slot_dto.cage_id, id_map)
                
                # Asignar jaula (ahora están todas libres)
                cage = await self.cage_repo.find_by_id(cage_id)
                if cage:
                    cage.assign_to_line()
                    await self.cage_repo.save(cage)
                
                slot_number = SlotNumber(slot_dto.slot_number)
                assignment = SlotAssignment(slot_number, cage_id)
                new_assignments.append(assignment)
            
            line.update_assignments(new_assignments)
            
            # Mapear IDs de componentes (los componentes se regeneran en cada update)
            id_map[dto.blower_config.id] = line.blower.id
            id_map[dto.selector_config.id] = line.selector.id
            
            for i, sensor in enumerate(line.sensors):
                id_map[dto.sensors_config[i].id] = sensor.id
            
            for i, doser in enumerate(line.dosers):
                id_map[dto.dosers_config[i].id] = doser.id
            
            # Guardar presentation_metadata de esta línea (si existe)
            line_presentation = request.presentation_data.get("lines", {}).get(dto.id, None)
            if line_presentation:
                updated_presentation = self._replace_temp_ids_in_presentation(
                    line_presentation, id_map
                )
                line.set_presentation_metadata(updated_presentation)
            
            await self.line_repo.save(line)
        
        # ====================================================================
        # FASE 5: RECONSTRUIR LAYOUT CON IDs REALES
        # ====================================================================
        
        # Cargar todos los agregados desde BD
        all_silos = await self.silo_repo.get_all()
        all_cages = await self.cage_repo.get_all()
        all_lines = await self.line_repo.get_all()
        
        # Convertir entidades de dominio a DTOs usando el mapper
        silos_dtos = [
            DomainToDTOMapper.silo_to_dto(silo)
            for silo in all_silos
        ]
        
        cages_dtos = [
            DomainToDTOMapper.cage_to_dto(cage)
            for cage in all_cages
        ]
        
        lines_dtos = [
            DomainToDTOMapper.feeding_line_to_dto(line)
            for line in all_lines
        ]
        
        # Reconstruir presentation_data desde los metadatos guardados en cada línea
        presentation_data = {
            "lines": {
                str(line.id): line.presentation_metadata
                for line in all_lines
                if line.presentation_metadata is not None
            }
        }
        
        return SystemLayoutDTO(
            silos=silos_dtos,
            cages=cages_dtos,
            feeding_lines=lines_dtos,
            presentation_data=presentation_data
        )

    # ========================================================================
    # MÉTODOS HELPER PRIVADOS
    # ========================================================================

    def _is_uuid(self, id_str: str) -> bool:
        try:
            uuid.UUID(id_str)
            return True
        except ValueError:
            return False

    def _build_blower_from_dto(self, dto: BlowerConfigDTO) -> Blower:
        name = BlowerName(dto.name)
        non_feeding_power = BlowerPowerPercentage(dto.non_feeding_power)
        blow_before_time = BlowDurationInSeconds(dto.blow_before_time)
        blow_after_time = BlowDurationInSeconds(dto.blow_after_time)
        
        return Blower(
            name=name,
            non_feeding_power=non_feeding_power,
            blow_before_time=blow_before_time,
            blow_after_time=blow_after_time
        )

    def _build_sensors_from_dto(self, sensors_dto: List[SensorConfigDTO]) -> List[Sensor]:
   
        sensors = []
        
        for dto in sensors_dto:
            try:
                sensor_type = SensorType[dto.sensor_type]
            except KeyError:
                raise ValueError(
                    f"Tipo de sensor inválido: '{dto.sensor_type}'. "
                    f"Valores válidos: {[t.name for t in SensorType]}"
                )
            
            name = SensorName(dto.name)
            
            sensor = Sensor(
                name=name,
                sensor_type=sensor_type
            )
            
            sensors.append(sensor)
        
        return sensors

    async def _build_dosers_from_dto(
        self,
        dosers_dto: List[DoserConfigDTO],
        id_map: Dict[str, Any]
    ) -> List[Doser]:

        dosers = []
        
        for dto in dosers_dto:
 
            silo_id = await self._resolve_and_assign_silo(dto.assigned_silo_id, id_map)
            
            name = DoserName(dto.name)
            dosing_range = DosingRange(
                min_rate=dto.min_rate,
                max_rate=dto.max_rate
            )
            current_rate = DosingRate(dto.current_rate)
            
            doser = Doser(
                name=name,
                assigned_silo_id=silo_id,
                doser_type=dto.doser_type,
                dosing_range=dosing_range,
                current_rate=current_rate
            )
            
            dosers.append(doser)
        
        return dosers

    def _build_selector_from_dto(self, dto: SelectorConfigDTO) -> Selector:
        name = SelectorName(dto.name)
        capacity = SelectorCapacity(dto.capacity)
        speed_profile = SelectorSpeedProfile(
            fast_speed=BlowerPowerPercentage(dto.fast_speed),
            slow_speed=BlowerPowerPercentage(dto.slow_speed)
        )
        
        return Selector(
            name=name,
            capacity=capacity,
            speed_profile=speed_profile
        )

    async def _resolve_and_assign_silo(
        self,
        silo_id_str: str,
        id_map: Dict[str, Any]
    ) -> SiloId:

        if silo_id_str in id_map:
            silo_id = id_map[silo_id_str]
        elif self._is_uuid(silo_id_str):
            silo_id = SiloId.from_string(silo_id_str)
        else:
            raise ValueError(f"El silo con ID temporal '{silo_id_str}' no fue creado")
        
        silo = await self.silo_repo.find_by_id(silo_id)
        if not silo:
            raise ValueError(f"El silo con ID '{silo_id_str}' no existe")
        
        # Validar que el silo no esté asignado a otro dosificador
        silo.assign_to_doser()
        await self.silo_repo.save(silo)
        
        return silo_id

    async def _resolve_cage_id(
        self,
        cage_id_str: str,
        id_map: Dict[str, Any]
    ) -> CageId:
        if cage_id_str in id_map:
            return id_map[cage_id_str]
        
        if self._is_uuid(cage_id_str):
            cage_id = CageId.from_string(cage_id_str)
            cage = await self.cage_repo.find_by_id(cage_id)
            if not cage:
                raise ValueError(f"La jaula con ID '{cage_id_str}' no existe")
            return cage_id
        
        raise ValueError(f"La jaula con ID temporal '{cage_id_str}' no fue creada")

    def _replace_temp_ids_in_presentation(
        self,
        presentation_metadata: Optional[Dict[str, Any]],
        id_map: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Reemplaza IDs temporales por IDs reales en los metadatos de presentación.
        
        Recorre la estructura de presentation_metadata (nodes, edges) y reemplaza
        cualquier ID temporal que esté en el id_map por su ID real correspondiente.
        
        Args:
            presentation_metadata: Diccionario con estructura de presentación (nodes, edges)
            id_map: Mapeo de IDs temporales a IDs reales
            
        Returns:
            Diccionario con IDs actualizados, o None si presentation_metadata es None
        """
        if not presentation_metadata:
            return None
        
        # Crear copia profunda para no mutar el original
        import copy
        updated_metadata = copy.deepcopy(presentation_metadata)
        
        # Reemplazar IDs en nodes
        if "nodes" in updated_metadata and isinstance(updated_metadata["nodes"], list):
            for node in updated_metadata["nodes"]:
                if isinstance(node, dict) and "id" in node:
                    node_id = node["id"]
                    if node_id in id_map:
                        node["id"] = str(id_map[node_id])
        
        # Reemplazar IDs en edges
        if "edges" in updated_metadata and isinstance(updated_metadata["edges"], list):
            for edge in updated_metadata["edges"]:
                if isinstance(edge, dict):
                    # Reemplazar edge.id
                    if "id" in edge and edge["id"] in id_map:
                        edge["id"] = str(id_map[edge["id"]])
                    
                    # Reemplazar edge.source
                    if "source" in edge and edge["source"] in id_map:
                        edge["source"] = str(id_map[edge["source"]])
                    
                    # Reemplazar edge.target
                    if "target" in edge and edge["target"] in id_map:
                        edge["target"] = str(id_map[edge["target"]])
        
        return updated_metadata
