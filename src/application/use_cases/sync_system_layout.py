import uuid
from typing import Any, Dict, List, Optional, Tuple

from api.models.system_layout import (
    BlowerConfigModel,
    CageConfigModel,
    CoolerConfigModel,
    DoserConfigModel,
    FeedingLineConfigModel,
    SelectorConfigModel,
    SensorConfigModel,
    SiloConfigModel,
    SlotAssignmentModel,
    SystemLayoutModel,
)
from application.services import DeltaCalculator, NameValidator, ResourceReleaser
from domain.aggregates.cage import Cage
from domain.aggregates.feeding_line.cooler import Cooler
from domain.aggregates.feeding_line.feeding_line import FeedingLine
from domain.aggregates.silo import Silo
from domain.entities.slot_assignment import SlotAssignment
from domain.enums import CageStatus, SensorType
from domain.exceptions import CageNotAvailableException, DuplicateLineNameException
from domain.factories import ComponentFactory
from domain.interfaces import IBlower, ICooler, IDoser, ISelector, ISensor
from domain.repositories import (
    ICageRepository,
    IFeedingLineRepository,
    ISiloRepository,
    ISlotAssignmentRepository,
)
from domain.value_objects import (
    BlowDurationInSeconds,
    BlowerName,
    BlowerPowerPercentage,
    CageId,
    CageName,
    CoolerName,
    CoolerPowerPercentage,
    DoserName,
    DosingRange,
    DosingRate,
    LineId,
    LineName,
    SelectorCapacity,
    SelectorName,
    SelectorSpeedProfile,
    SensorName,
    SiloId,
    SiloName,
    Weight,
)


class SyncSystemLayoutUseCase:
    def __init__(
        self,
        line_repo: IFeedingLineRepository,
        silo_repo: ISiloRepository,
        cage_repo: ICageRepository,
        slot_assignment_repo: ISlotAssignmentRepository,
        component_factory: ComponentFactory,
    ):
        self.line_repo = line_repo
        self.silo_repo = silo_repo
        self.cage_repo = cage_repo
        self.slot_assignment_repo = slot_assignment_repo
        self.component_factory = component_factory

    async def execute(
        self, request: SystemLayoutModel
    ) -> Tuple[
        List[Silo], List[Cage], List[FeedingLine], Dict[LineId, List[SlotAssignment]]
    ]:
        id_map: Dict[str, Any] = {}

        # FASE 1: CÁLCULO DE DELTA
        delta = await DeltaCalculator.calculate(
            request, self.line_repo, self.silo_repo, self.cage_repo
        )

        print("delta: ", delta)

        # FASE 2: EJECUTAR ELIMINACIONES
        await self._execute_deletions(delta)

        # FASE 3: EJECUTAR CREACIONES (y Mapear IDs)
        await self._execute_creations(delta, id_map)

        # FASE 4: EJECUTAR ACTUALIZACIONES
        await self._execute_updates(delta, id_map)

        # FASE 5: RECONSTRUIR LAYOUT CON IDs REALES
        return await self._rebuild_layout()

    # ========================================================================
    # MÉTODOS HELPER PRIVADOS
    # ========================================================================

    def _is_uuid(self, id_str: str) -> bool:
        try:
            uuid.UUID(id_str)
            return True
        except ValueError:
            return False

    def _build_blower_from_model(self, model: BlowerConfigModel) -> IBlower:
        name = BlowerName(model.name)
        non_feeding_power = BlowerPowerPercentage(model.non_feeding_power)
        blow_before_time = BlowDurationInSeconds(model.blow_before_time)
        blow_after_time = BlowDurationInSeconds(model.blow_after_time)

        return self.component_factory.create_blower(
            blower_type=model.blower_type,
            name=name,
            non_feeding_power=non_feeding_power,
            blow_before_time=blow_before_time,
            blow_after_time=blow_after_time,
        )

    def _build_sensors_from_model(
        self, sensors_model: List[SensorConfigModel]
    ) -> List[ISensor]:
        sensors = []

        for model in sensors_model:
            try:
                sensor_type = SensorType[model.sensor_type]
            except KeyError:
                raise ValueError(
                    f"Tipo de sensor inválido: '{model.sensor_type}'. "
                    f"Valores válidos: {[t.name for t in SensorType]}"
                )

            name = SensorName(model.name)

            sensor = self.component_factory.create_sensor(
                sensor_type=sensor_type, name=name
            )

            sensors.append(sensor)

        return sensors

    async def _build_dosers_from_model(
        self, dosers_model: List[DoserConfigModel], id_map: Dict[str, Any]
    ) -> List[IDoser]:
        dosers = []

        for model in dosers_model:
            silo_id = await self._resolve_and_assign_silo(
                model.assigned_silo_id, id_map
            )

            name = DoserName(model.name)
            dosing_range = DosingRange(min_rate=model.min_rate, max_rate=model.max_rate)
            current_rate = DosingRate(model.current_rate)

            doser = self.component_factory.create_doser(
                doser_type=model.doser_type,
                name=name,
                assigned_silo_id=silo_id,
                dosing_range=dosing_range,
                current_rate=current_rate,
            )

            dosers.append(doser)

        return dosers

    def _build_selector_from_model(self, model: SelectorConfigModel) -> ISelector:
        name = SelectorName(model.name)
        capacity = SelectorCapacity(model.capacity)
        speed_profile = SelectorSpeedProfile(
            fast_speed=BlowerPowerPercentage(model.fast_speed),
            slow_speed=BlowerPowerPercentage(model.slow_speed),
        )

        return self.component_factory.create_selector(
            selector_type=model.selector_type,
            name=name,
            capacity=capacity,
            speed_profile=speed_profile,
        )

    def _build_cooler_from_model(self, model: CoolerConfigModel) -> ICooler:
        """Construye una instancia de Cooler desde el modelo de configuración."""
        name = CoolerName(model.name)
        cooling_power = CoolerPowerPercentage(model.cooling_power_percentage)

        cooler = Cooler(
            name=name,
            cooling_power_percentage=cooling_power,
            is_on=model.is_on,
        )

        return cooler

    async def _resolve_and_assign_silo(
        self, silo_id_str: str, id_map: Dict[str, Any]
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
        self, cage_id_str: str, id_map: Dict[str, Any]
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

    # ========================================================================
    # MÉTODOS DE ORQUESTACIÓN DE FASES
    # ========================================================================

    async def _execute_deletions(self, delta) -> None:
        """Elimina agregados que no están en el request."""
        # Primero liberar slots de líneas a eliminar
        for line_id in delta.lines_to_delete:
            await self.slot_assignment_repo.delete_by_line(line_id)
            await self.line_repo.delete(line_id)

        for silo_id in delta.silos_to_delete:
            await self.silo_repo.delete(silo_id)

        # Para jaulas eliminadas, primero eliminar sus asignaciones
        for cage_id in delta.cages_to_delete:
            await self.slot_assignment_repo.delete_by_cage(cage_id)
            await self.cage_repo.delete(cage_id)

    async def _execute_creations(self, delta, id_map: Dict[str, Any]) -> None:
        """Crea nuevos agregados y mapea IDs temporales a reales."""
        await self._create_silos(delta.silos_to_create, id_map)
        await self._create_cages(delta.cages_to_create, id_map)
        await self._create_feeding_lines(delta.lines_to_create, id_map)

    async def _create_silos(self, silos_dtos, id_map: Dict[str, Any]) -> None:
        """Crea silos y mapea sus IDs."""
        for dto in silos_dtos:
            await NameValidator.validate_unique_silo_name(
                dto.name, exclude_id=None, repo=self.silo_repo
            )

            name = SiloName(dto.name)
            capacity = Weight.from_kg(dto.capacity)
            stock_level = Weight.zero()

            new_silo = Silo(name=name, capacity=capacity, stock_level=stock_level)

            await self.silo_repo.save(new_silo)
            id_map[dto.id] = new_silo.id

    async def _create_cages(self, cages_dtos, id_map: Dict[str, Any]) -> None:
        """Crea jaulas y mapea sus IDs."""
        for dto in cages_dtos:
            await NameValidator.validate_unique_cage_name(
                dto.name, exclude_id=None, repo=self.cage_repo
            )

            name = CageName(dto.name)
            new_cage = Cage(name=name)

            await self.cage_repo.save(new_cage)
            id_map[dto.id] = new_cage.id

    async def _create_feeding_lines(self, lines_dtos, id_map: Dict[str, Any]) -> None:
        """Crea líneas de alimentación y mapea sus IDs."""
        for dto in lines_dtos:
            await NameValidator.validate_unique_line_name(
                dto.line_name, exclude_id=None, repo=self.line_repo
            )

            # Validar capacidad del selector vs número de slots
            if len(dto.slot_assignments) > dto.selector_config.capacity:
                raise ValueError(
                    f"La línea '{dto.line_name}' tiene {len(dto.slot_assignments)} slots "
                    f"pero el selector solo tiene capacidad para {dto.selector_config.capacity}"
                )

            blower = self._build_blower_from_model(dto.blower_config)
            cooler = (
                self._build_cooler_from_model(dto.cooler_config)
                if dto.cooler_config
                else None
            )
            sensors = self._build_sensors_from_model(dto.sensors_config)
            dosers = await self._build_dosers_from_model(dto.dosers_config, id_map)
            selector = self._build_selector_from_model(dto.selector_config)

            new_line = FeedingLine.create(
                name=LineName(dto.line_name),
                blower=blower,
                dosers=dosers,
                selector=selector,
                sensors=sensors,
                cooler=cooler,
            )

            # PASO 1: Guardar línea PRIMERO (necesitamos line_id)
            await self.line_repo.save(new_line)
            id_map[dto.id] = new_line.id

            # PASO 2: Asignar cages a slots usando SlotAssignment
            await self._assign_cages_to_line(
                new_line.id, dto.slot_assignments, selector.capacity.value, id_map
            )

    async def _assign_cages_to_line(
        self,
        line_id: LineId,
        slot_assignments_dto: List[SlotAssignmentModel],
        selector_capacity: int,
        id_map: Dict[str, Any],
    ) -> None:
        """Asigna jaulas a slots de una línea."""
        for slot_dto in slot_assignments_dto:
            # Validar que el slot_number esté en el rango válido
            if slot_dto.slot_number < 1 or slot_dto.slot_number > selector_capacity:
                raise ValueError(
                    f"El slot {slot_dto.slot_number} está fuera del rango válido "
                    f"(1-{selector_capacity})"
                )

            cage_id = await self._resolve_cage_id(slot_dto.cage_id, id_map)
            cage = await self.cage_repo.find_by_id(cage_id)

            if not cage:
                raise ValueError(f"La jaula con ID '{slot_dto.cage_id}' no existe")

            # Validar que la jaula esté disponible
            if cage.status != CageStatus.AVAILABLE:
                raise CageNotAvailableException(
                    f"La jaula '{cage.name}' no está disponible (estado: {cage.status.value})"
                )

            # Validar que no haya otra cage en el mismo slot
            existing_assignment = await self.slot_assignment_repo.find_by_line_and_slot(
                line_id, slot_dto.slot_number
            )
            if existing_assignment:
                existing_cage = await self.cage_repo.find_by_id(
                    existing_assignment.cage_id
                )
                cage_name = existing_cage.name if existing_cage else "desconocida"
                raise ValueError(
                    f"El slot {slot_dto.slot_number} ya está ocupado por la jaula '{cage_name}'"
                )

            # Validar que la jaula no esté asignada a otro slot
            existing_cage_assignment = await self.slot_assignment_repo.find_by_cage(
                cage_id
            )
            if existing_cage_assignment:
                raise ValueError(f"La jaula '{cage.name}' ya está asignada a otro slot")

            # Crear asignación de slot
            slot_assignment = SlotAssignment.create(
                line_id=line_id,
                cage_id=cage_id,
                slot_number=slot_dto.slot_number,
            )
            await self.slot_assignment_repo.save(slot_assignment)

            # Marcar jaula como en uso
            cage.set_in_use()
            await self.cage_repo.save(cage)

    async def _execute_updates(self, delta, id_map: Dict[str, Any]) -> None:
        """Actualiza agregados existentes."""
        await self._update_silos(delta.silos_to_update)
        await self._update_cages(delta.cages_to_update)
        await self._update_feeding_lines(delta.lines_to_update, id_map)

    async def _update_silos(self, silos_to_update) -> None:
        """Actualiza silos existentes."""
        for silo_id, dto in silos_to_update.items():
            silo = await self.silo_repo.find_by_id(silo_id)
            if not silo:
                continue

            # Validar FA2: Nombre duplicado (solo si cambió el nombre)
            if str(silo.name) != dto.name:
                await NameValidator.validate_unique_silo_name(
                    dto.name, exclude_id=silo_id, repo=self.silo_repo
                )
                silo.name = SiloName(dto.name)

            silo.capacity = Weight.from_kg(dto.capacity)
            await self.silo_repo.save(silo)

    async def _update_cages(self, cages_to_update) -> None:
        """Actualiza jaulas existentes."""
        for cage_id, dto in cages_to_update.items():
            cage = await self.cage_repo.find_by_id(cage_id)
            if not cage:
                continue

            # Validar FA2: Nombre duplicado (solo si cambió el nombre)
            if str(cage.name) != dto.name:
                await NameValidator.validate_unique_cage_name(
                    dto.name, exclude_id=cage_id, repo=self.cage_repo
                )
                cage.rename(CageName(dto.name))

            await self.cage_repo.save(cage)

    async def _update_feeding_lines(
        self, lines_to_update, id_map: Dict[str, Any]
    ) -> None:
        """Actualiza líneas de alimentación existentes."""
        # Liberar recursos (ResourceReleaser ya actualizado)
        lines_to_release = []
        for line_id in lines_to_update.keys():
            line = await self.line_repo.find_by_id(line_id)
            if line:
                lines_to_release.append(line)

        await ResourceReleaser.release_all_from_lines(
            lines_to_release,
            self.silo_repo,
            self.cage_repo,
            self.slot_assignment_repo,
        )

        # Reasignar recursos
        for line_id, dto in lines_to_update.items():
            line = await self.line_repo.find_by_id(line_id)
            if not line:
                continue

            # Validar nombre único si cambió
            if str(line.name) != dto.line_name:
                await NameValidator.validate_unique_line_name(
                    dto.line_name, exclude_id=line_id, repo=self.line_repo
                )
                line.name = LineName(dto.line_name)

            # Validar capacidad del selector
            if len(dto.slot_assignments) > dto.selector_config.capacity:
                raise ValueError(
                    f"La línea '{dto.line_name}' tiene {len(dto.slot_assignments)} slots "
                    f"pero el selector solo tiene capacidad para {dto.selector_config.capacity}"
                )

            # Actualizar componentes
            blower = self._build_blower_from_model(dto.blower_config)
            cooler = (
                self._build_cooler_from_model(dto.cooler_config)
                if dto.cooler_config
                else None
            )
            sensors = self._build_sensors_from_model(dto.sensors_config)
            dosers = await self._build_dosers_from_model(dto.dosers_config, id_map)
            selector = self._build_selector_from_model(dto.selector_config)

            line.update_components(blower, dosers, selector, sensors, cooler)
            await self.line_repo.save(line)

            # Asignar nuevas cages (ResourceReleaser ya liberó las anteriores)
            await self._assign_cages_to_line(
                line_id, dto.slot_assignments, selector.capacity.value, id_map
            )

    async def _rebuild_layout(
        self,
    ) -> Tuple[
        List[Silo], List[Cage], List[FeedingLine], Dict[LineId, List[SlotAssignment]]
    ]:
        """Reconstruye el layout completo con IDs reales desde BD."""
        all_silos = await self.silo_repo.get_all()
        all_cages = await self.cage_repo.list()
        all_lines = await self.line_repo.get_all()

        # Cargar slot assignments agrupados por línea
        slot_assignments_by_line: Dict[LineId, List[SlotAssignment]] = {}
        for line in all_lines:
            assignments = await self.slot_assignment_repo.find_by_line(line.id)
            slot_assignments_by_line[line.id] = assignments

        return (all_silos, all_cages, all_lines, slot_assignments_by_line)
