from dataclasses import dataclass
from typing import Optional

from application.dtos.silo_dtos import SiloInventoryBatchDTO


@dataclass
class CreateSiloBatchRequest:
    food_id: str
    quantity_kg: float
    operator_id: str


@dataclass
class UpdateSiloBatchRequest:
    operator_id: str
    food_id: Optional[str] = None
    remaining_quantity_kg: Optional[float] = None


@dataclass
class MoveSiloBatchRequest:
    operator_id: str
    before_batch_id: Optional[str] = None
    after_batch_id: Optional[str] = None


@dataclass
class WithdrawSiloBatchRequest:
    operator_id: str


@dataclass
class TransferSiloStockRequest:
    destination_silo_id: str
    quantity_kg: float
    operator_id: str


@dataclass
class TransferSiloStockResponse:
    source_silo_id: str
    destination_silo_id: str
    quantity_kg: float
    transferred_batches: list[SiloInventoryBatchDTO]


@dataclass
class ListSiloBatchesResponse:
    batches: list[SiloInventoryBatchDTO]
    offset: int
    limit: int
