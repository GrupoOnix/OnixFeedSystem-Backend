from typing import Dict
from uuid import UUID

from application.dtos.manual_feeding_config_dtos import (
    LastValidCyclicCageConfigPayload,
    LastSelectedFeedingModePayload,
    LastSelectedFeedingModeResponse,
    LastValidCyclicFeedingConfigPayload,
    LastValidCyclicFeedingConfigResponse,
    LastValidManualFeedingConfigPayload,
    LastValidManualFeedingConfigResponse,
)
from domain.repositories import (
    ICageGroupRepository,
    ICageRepository,
    IFeedingLineRepository,
    ISiloRepository,
    ISlotAssignmentRepository,
)
from domain.value_objects import CageId, LineId, SiloId
from domain.value_objects.identifiers import CageGroupId, DoserId
from infrastructure.persistence.models.last_selected_feeding_mode_model import (
    LastSelectedFeedingModeModel,
)
from infrastructure.persistence.models.last_valid_cyclic_feeding_config_model import (
    LastValidCyclicFeedingConfigModel,
)
from infrastructure.persistence.models.last_valid_manual_feeding_config_model import (
    LastValidManualFeedingConfigModel,
)
from infrastructure.persistence.repositories.last_selected_feeding_mode_repository import (
    LastSelectedFeedingModeRepository,
)
from infrastructure.persistence.repositories.last_valid_cyclic_feeding_config_repository import (
    LastValidCyclicFeedingConfigRepository,
)
from infrastructure.persistence.repositories.last_valid_manual_feeding_config_repository import (
    LastValidManualFeedingConfigRepository,
)


class ListLastValidManualFeedingConfigsUseCase:
    def __init__(
        self,
        config_repository: LastValidManualFeedingConfigRepository,
        line_repository: IFeedingLineRepository,
        cage_repository: ICageRepository,
        silo_repository: ISiloRepository,
        slot_assignment_repository: ISlotAssignmentRepository,
    ):
        self.config_repo = config_repository
        self.line_repo = line_repository
        self.cage_repo = cage_repository
        self.silo_repo = silo_repository
        self.slot_assignment_repo = slot_assignment_repository

    async def execute(self) -> Dict[str, LastValidManualFeedingConfigResponse]:
        configs = await self.config_repo.list()
        responses = [await _to_response(config, self) for config in configs]
        return {response.line_id: response for response in responses}


class GetLastValidManualFeedingConfigUseCase:
    def __init__(
        self,
        config_repository: LastValidManualFeedingConfigRepository,
        line_repository: IFeedingLineRepository,
        cage_repository: ICageRepository,
        silo_repository: ISiloRepository,
        slot_assignment_repository: ISlotAssignmentRepository,
    ):
        self.config_repo = config_repository
        self.line_repo = line_repository
        self.cage_repo = cage_repository
        self.silo_repo = silo_repository
        self.slot_assignment_repo = slot_assignment_repository

    async def execute(self, line_id: str) -> LastValidManualFeedingConfigResponse:
        line_uuid = UUID(line_id)
        config = await self.config_repo.find_by_line_id(line_uuid)
        if not config:
            raise LookupError(f"No existe configuración manual válida para la línea {line_id}")
        return await _to_response(config, self)


class UpsertLastValidManualFeedingConfigUseCase:
    def __init__(
        self,
        config_repository: LastValidManualFeedingConfigRepository,
        line_repository: IFeedingLineRepository,
        cage_repository: ICageRepository,
        silo_repository: ISiloRepository,
        slot_assignment_repository: ISlotAssignmentRepository,
    ):
        self.config_repo = config_repository
        self.line_repo = line_repository
        self.cage_repo = cage_repository
        self.silo_repo = silo_repository
        self.slot_assignment_repo = slot_assignment_repository

    async def execute(
        self,
        line_id: str,
        request: LastValidManualFeedingConfigPayload,
        updated_by: str | None = None,
    ) -> LastValidManualFeedingConfigResponse:
        line_uuid = UUID(line_id)
        silo_uuid = UUID(request.target_silo_id)
        cage_uuid = UUID(request.target_cage_id)

        await _assert_valid_for_save(
            line_id=line_id,
            line_uuid=line_uuid,
            silo_uuid=silo_uuid,
            cage_uuid=cage_uuid,
            line_repo=self.line_repo,
            cage_repo=self.cage_repo,
            silo_repo=self.silo_repo,
            slot_assignment_repo=self.slot_assignment_repo,
        )

        config = await self.config_repo.upsert_by_line_id(
            line_id=line_uuid,
            target_silo_id=silo_uuid,
            target_cage_id=cage_uuid,
            target_amount_kg=request.target_amount_kg,
            dosing_rate_kg_per_min=request.dosing_rate_kg_per_min,
            dosing_unit=request.dosing_unit,
            blower_power_percentage=request.blower_power_percentage,
            updated_by=updated_by,
        )
        return await _to_response(config, self)


class ListLastSelectedFeedingModesUseCase:
    def __init__(
        self,
        mode_repository: LastSelectedFeedingModeRepository,
        line_repository: IFeedingLineRepository,
    ):
        self.mode_repo = mode_repository
        self.line_repo = line_repository

    async def execute(self) -> Dict[str, LastSelectedFeedingModeResponse]:
        modes = await self.mode_repo.list()
        responses = [_mode_to_response(mode) for mode in modes]
        return {response.line_id: response for response in responses}


class GetLastSelectedFeedingModeUseCase:
    def __init__(
        self,
        mode_repository: LastSelectedFeedingModeRepository,
        line_repository: IFeedingLineRepository,
    ):
        self.mode_repo = mode_repository
        self.line_repo = line_repository

    async def execute(self, line_id: str) -> LastSelectedFeedingModeResponse:
        line_uuid = UUID(line_id)
        mode = await self.mode_repo.find_by_line_id(line_uuid)
        if not mode:
            raise LookupError(f"No existe opción seleccionada para la línea {line_id}")
        return _mode_to_response(mode)


class UpsertLastSelectedFeedingModeUseCase:
    def __init__(
        self,
        mode_repository: LastSelectedFeedingModeRepository,
        line_repository: IFeedingLineRepository,
    ):
        self.mode_repo = mode_repository
        self.line_repo = line_repository

    async def execute(
        self,
        line_id: str,
        request: LastSelectedFeedingModePayload,
        updated_by: str | None = None,
    ) -> LastSelectedFeedingModeResponse:
        line_uuid = UUID(line_id)
        line = await self.line_repo.find_by_id(LineId(line_uuid))
        if not line:
            raise ValueError(f"Línea con ID {line_id} no encontrada")

        mode = await self.mode_repo.upsert_by_line_id(
            line_id=line_uuid,
            selected_mode=request.selected_mode,
            updated_by=updated_by,
        )
        return _mode_to_response(mode)


class ListLastValidCyclicFeedingConfigsUseCase:
    def __init__(
        self,
        config_repository: LastValidCyclicFeedingConfigRepository,
        line_repository: IFeedingLineRepository,
        cage_repository: ICageRepository,
        cage_group_repository: ICageGroupRepository,
        silo_repository: ISiloRepository,
        slot_assignment_repository: ISlotAssignmentRepository,
    ):
        self.config_repo = config_repository
        self.line_repo = line_repository
        self.cage_repo = cage_repository
        self.cage_group_repo = cage_group_repository
        self.silo_repo = silo_repository
        self.slot_assignment_repo = slot_assignment_repository

    async def execute(self) -> Dict[str, LastValidCyclicFeedingConfigResponse]:
        configs = await self.config_repo.list()
        responses = [await _cyclic_to_response(config, self) for config in configs]
        return {response.line_id: response for response in responses}


class GetLastValidCyclicFeedingConfigUseCase:
    def __init__(
        self,
        config_repository: LastValidCyclicFeedingConfigRepository,
        line_repository: IFeedingLineRepository,
        cage_repository: ICageRepository,
        cage_group_repository: ICageGroupRepository,
        silo_repository: ISiloRepository,
        slot_assignment_repository: ISlotAssignmentRepository,
    ):
        self.config_repo = config_repository
        self.line_repo = line_repository
        self.cage_repo = cage_repository
        self.cage_group_repo = cage_group_repository
        self.silo_repo = silo_repository
        self.slot_assignment_repo = slot_assignment_repository

    async def execute(self, line_id: str) -> LastValidCyclicFeedingConfigResponse:
        line_uuid = UUID(line_id)
        config = await self.config_repo.find_by_line_id(line_uuid)
        if not config:
            raise LookupError(f"No existe configuración cíclica válida para la línea {line_id}")
        return await _cyclic_to_response(config, self)


class UpsertLastValidCyclicFeedingConfigUseCase:
    def __init__(
        self,
        config_repository: LastValidCyclicFeedingConfigRepository,
        line_repository: IFeedingLineRepository,
        cage_repository: ICageRepository,
        cage_group_repository: ICageGroupRepository,
        silo_repository: ISiloRepository,
        slot_assignment_repository: ISlotAssignmentRepository,
    ):
        self.config_repo = config_repository
        self.line_repo = line_repository
        self.cage_repo = cage_repository
        self.cage_group_repo = cage_group_repository
        self.silo_repo = silo_repository
        self.slot_assignment_repo = slot_assignment_repository

    async def execute(
        self,
        line_id: str,
        request: LastValidCyclicFeedingConfigPayload,
        updated_by: str | None = None,
    ) -> LastValidCyclicFeedingConfigResponse:
        line_uuid = UUID(line_id)
        group_uuid = UUID(request.group_id)
        doser_uuid = UUID(request.doser_id)

        await _assert_cyclic_valid_for_save(
            line_id=line_id,
            line_uuid=line_uuid,
            group_uuid=group_uuid,
            doser_uuid=doser_uuid,
            cage_configs=request.cage_configs,
            line_repo=self.line_repo,
            cage_repo=self.cage_repo,
            cage_group_repo=self.cage_group_repo,
            silo_repo=self.silo_repo,
            slot_assignment_repo=self.slot_assignment_repo,
        )

        config = await self.config_repo.upsert_by_line_id(
            line_id=line_uuid,
            group_id=group_uuid,
            doser_id=doser_uuid,
            visits=_resolve_global_cyclic_visits(request),
            blower_power_percentage=request.blower_power_percentage,
            cage_configs=[
                _cyclic_cage_config_dump_with_visits(cage_config, request.visits)
                for cage_config in request.cage_configs
            ],
            updated_by=updated_by,
        )
        return await _cyclic_to_response(config, self)


async def _assert_valid_for_save(
    *,
    line_id: str,
    line_uuid: UUID,
    silo_uuid: UUID,
    cage_uuid: UUID,
    line_repo: IFeedingLineRepository,
    cage_repo: ICageRepository,
    silo_repo: ISiloRepository,
    slot_assignment_repo: ISlotAssignmentRepository,
) -> None:
    line = await line_repo.find_by_id(LineId(line_uuid))
    if not line:
        raise ValueError(f"Línea con ID {line_id} no encontrada")

    silo = await silo_repo.find_by_id(SiloId(silo_uuid))
    if not silo:
        raise ValueError(f"Silo con ID {silo_uuid} no encontrado")

    if not any(doser.assigned_silo_id.value == silo_uuid for doser in line.dosers):
        raise ValueError(f"El silo {silo_uuid} no pertenece a la línea {line_id}")

    cage = await cage_repo.find_by_id(CageId(cage_uuid))
    if not cage:
        raise ValueError(f"Jaula con ID {cage_uuid} no encontrada")

    assignment = await slot_assignment_repo.find_by_cage(CageId(cage_uuid))
    if not assignment or assignment.line_id.value != line_uuid:
        raise ValueError(f"La jaula {cage_uuid} no pertenece a la línea {line_id}")


async def _assert_cyclic_valid_for_save(
    *,
    line_id: str,
    line_uuid: UUID,
    group_uuid: UUID,
    doser_uuid: UUID,
    cage_configs,
    line_repo: IFeedingLineRepository,
    cage_repo: ICageRepository,
    cage_group_repo: ICageGroupRepository,
    silo_repo: ISiloRepository,
    slot_assignment_repo: ISlotAssignmentRepository,
) -> None:
    line = await line_repo.find_by_id(LineId(line_uuid))
    if not line:
        raise ValueError(f"Línea con ID {line_id} no encontrada")

    selected_doser = line.get_doser_by_id(DoserId(doser_uuid))
    if not selected_doser:
        raise ValueError(f"El doser {doser_uuid} no existe en la línea {line_id}")

    silo = await silo_repo.find_by_id(selected_doser.assigned_silo_id)
    if not silo:
        raise ValueError(f"El doser {doser_uuid} no tiene un silo asignado")

    group = await cage_group_repo.find_by_id(CageGroupId(group_uuid))
    if not group:
        raise ValueError(f"Grupo con ID {group_uuid} no encontrado")

    group_cage_ids = await _get_existing_group_cage_ids_for_line(
        group_cage_ids={cage_id.value for cage_id in group.cage_ids},
        line_uuid=line_uuid,
        cage_repo=cage_repo,
        slot_assignment_repo=slot_assignment_repo,
    )
    if not group_cage_ids:
        raise ValueError(f"El grupo {group_uuid} no contiene jaulas válidas para la línea {line_id}")

    request_cage_ids = {UUID(config.cage_id) for config in cage_configs}

    missing_in_request = group_cage_ids - request_cage_ids
    if missing_in_request:
        raise ValueError(
            "Las siguientes jaulas del grupo no están en la configuración: "
            f"{', '.join(str(cage_id) for cage_id in missing_in_request)}"
        )

    extra_in_request = request_cage_ids - group_cage_ids
    if extra_in_request:
        raise ValueError(
            "Las siguientes jaulas no pertenecen al grupo: "
            f"{', '.join(str(cage_id) for cage_id in extra_in_request)}"
        )

    for cage_config in cage_configs:
        cage_uuid = UUID(cage_config.cage_id)
        cage = await cage_repo.find_by_id(CageId(cage_uuid))
        if not cage:
            raise ValueError(f"Jaula con ID {cage_uuid} no encontrada")

        assignment = await slot_assignment_repo.find_by_cage(CageId(cage_uuid))
        if not assignment or assignment.line_id.value != line_uuid:
            raise ValueError(f"La jaula {cage_uuid} no pertenece a la línea {line_id}")

        if cage_config.mode != "FASTING" and cage_config.rate_kg_per_min > selected_doser.max_rate_kg_per_min:
            raise ValueError(
                f"La tasa de la jaula {cage_uuid} ({cage_config.rate_kg_per_min} kg/min) "
                f"excede la capacidad máxima del doser ({selected_doser.max_rate_kg_per_min} kg/min)"
            )


async def _get_existing_group_cage_ids_for_line(
    *,
    group_cage_ids: set[UUID],
    line_uuid: UUID,
    cage_repo: ICageRepository,
    slot_assignment_repo: ISlotAssignmentRepository,
) -> set[UUID]:
    valid_cage_ids: set[UUID] = set()
    for cage_uuid in group_cage_ids:
        cage = await cage_repo.find_by_id(CageId(cage_uuid))
        if not cage:
            continue

        assignment = await slot_assignment_repo.find_by_cage(CageId(cage_uuid))
        if assignment and assignment.line_id.value == line_uuid:
            valid_cage_ids.add(cage_uuid)

    return valid_cage_ids


async def _is_valid_against_current_layout(
    config: LastValidManualFeedingConfigModel,
    use_case,
) -> bool:
    line = await use_case.line_repo.find_by_id(LineId(config.line_id))
    if not line:
        return False

    silo = await use_case.silo_repo.find_by_id(SiloId(config.target_silo_id))
    if not silo:
        return False

    if not any(doser.assigned_silo_id.value == config.target_silo_id for doser in line.dosers):
        return False

    cage = await use_case.cage_repo.find_by_id(CageId(config.target_cage_id))
    if not cage:
        return False

    assignment = await use_case.slot_assignment_repo.find_by_cage(CageId(config.target_cage_id))
    return bool(assignment and assignment.line_id.value == config.line_id)


async def _to_response(
    config: LastValidManualFeedingConfigModel,
    use_case,
) -> LastValidManualFeedingConfigResponse:
    return LastValidManualFeedingConfigResponse(
        id=str(config.id),
        line_id=str(config.line_id),
        target_silo_id=str(config.target_silo_id),
        target_cage_id=str(config.target_cage_id),
        target_amount_kg=config.target_amount_kg,
        dosing_rate_kg_per_min=config.dosing_rate_kg_per_min,
        dosing_unit=config.dosing_unit,
        blower_power_percentage=config.blower_power_percentage,
        updated_by=config.updated_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
        is_valid_against_current_layout=await _is_valid_against_current_layout(config, use_case),
    )


def _mode_to_response(mode: LastSelectedFeedingModeModel) -> LastSelectedFeedingModeResponse:
    return LastSelectedFeedingModeResponse(
        id=str(mode.id),
        line_id=str(mode.line_id),
        selected_mode=mode.selected_mode,  # type: ignore[arg-type]
        updated_by=mode.updated_by,
        created_at=mode.created_at,
        updated_at=mode.updated_at,
    )


def _resolve_global_cyclic_visits(request: LastValidCyclicFeedingConfigPayload) -> int:
    if request.visits is not None:
        return request.visits
    return max(
        (
            cage_config.visits or 0
            for cage_config in request.cage_configs
            if cage_config.mode != "FASTING"
        ),
        default=1,
    )


def _cyclic_cage_config_dump_with_visits(
    cage_config: LastValidCyclicCageConfigPayload,
    fallback_visits: int | None,
) -> dict:
    data = cage_config.model_dump()
    if data["mode"] != "FASTING" and data.get("visits") is None:
        data["visits"] = fallback_visits
    return data


async def _is_cyclic_valid_against_current_layout(
    config: LastValidCyclicFeedingConfigModel,
    use_case,
) -> bool:
    try:
        cage_configs = [
            _cyclic_cage_config_with_legacy_visits(cage_config, config.visits)
            for cage_config in config.cage_configs
        ]
        payload = LastValidCyclicFeedingConfigPayload(
            group_id=str(config.group_id),
            doser_id=str(config.doser_id),
            visits=config.visits,
            blower_power_percentage=config.blower_power_percentage,
            cage_configs=cage_configs,
        )
        await _assert_cyclic_valid_for_save(
            line_id=str(config.line_id),
            line_uuid=config.line_id,
            group_uuid=config.group_id,
            doser_uuid=config.doser_id,
            cage_configs=payload.cage_configs,
            line_repo=use_case.line_repo,
            cage_repo=use_case.cage_repo,
            cage_group_repo=use_case.cage_group_repo,
            silo_repo=use_case.silo_repo,
            slot_assignment_repo=use_case.slot_assignment_repo,
        )
    except (TypeError, ValueError):
        return False
    return True


def _cyclic_cage_config_with_legacy_visits(
    cage_config: dict,
    fallback_visits: int,
) -> dict:
    if cage_config.get("mode") == "FASTING":
        return dict(cage_config)
    return {**cage_config, "visits": cage_config.get("visits", fallback_visits)}


async def _cyclic_to_response(
    config: LastValidCyclicFeedingConfigModel,
    use_case,
) -> LastValidCyclicFeedingConfigResponse:
    return LastValidCyclicFeedingConfigResponse(
        id=str(config.id),
        line_id=str(config.line_id),
        group_id=str(config.group_id),
        doser_id=str(config.doser_id),
        visits=config.visits,
        blower_power_percentage=config.blower_power_percentage,
        cage_configs=[
            LastValidCyclicCageConfigPayload(**_cyclic_cage_config_with_legacy_visits(cage_config, config.visits))
            for cage_config in config.cage_configs
        ],
        updated_by=config.updated_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
        is_valid_against_current_layout=await _is_cyclic_valid_against_current_layout(config, use_case),
    )
