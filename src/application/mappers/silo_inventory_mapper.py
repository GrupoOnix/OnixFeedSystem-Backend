from application.dtos.silo_dtos import SiloBatchFoodDTO, SiloInventoryBatchDTO
from domain.entities.silo_inventory import SiloInventoryBatch


def to_batch_dto(batch: SiloInventoryBatch) -> SiloInventoryBatchDTO:
    food = None
    if batch.food_id and batch.food_name and batch.food_code and batch.food_provider:
        food = SiloBatchFoodDTO(
            id=str(batch.food_id),
            name=batch.food_name,
            code=batch.food_code,
            provider=batch.food_provider,
        )
    return SiloInventoryBatchDTO(
        id=str(batch.id),
        food=food,
        remaining_quantity_kg=batch.remaining_quantity_kg,
        reserved_quantity_kg=batch.reserved_quantity_kg,
        available_quantity_kg=batch.available_quantity_kg,
        position=batch.position,
        status=batch.status.value,
        received_at=batch.received_at,
        created_by_operator_id=batch.created_by_operator_id,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
    )
