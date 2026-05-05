from typing import Dict
from uuid import UUID

from application.dtos.manual_feeding_config_dtos import (
    LastValidManualFeedingConfigPayload,
    LastValidManualFeedingConfigResponse,
)
from domain.repositories import (
    ICageRepository,
    IFeedingLineRepository,
    ISiloRepository,
    ISlotAssignmentRepository,
)
from domain.value_objects import CageId, LineId, SiloId
from infrastructure.persistence.models.last_valid_manual_feeding_config_model import (
    LastValidManualFeedingConfigModel,
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
