from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class SiloInventoryBatchStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DEPLETED = "DEPLETED"
    ARCHIVED = "ARCHIVED"


class SiloInventoryMovementType(str, Enum):
    INITIAL_LOAD = "INITIAL_LOAD"
    ADJUSTMENT = "ADJUSTMENT"
    WITHDRAWAL = "WITHDRAWAL"
    CONSUMPTION = "CONSUMPTION"
    FOOD_CHANGED = "FOOD_CHANGED"
    REORDERED = "REORDERED"
    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"


class SiloStockReservationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    CONSUMED = "CONSUMED"


@dataclass(frozen=True)
class SiloInventoryBatch:
    id: UUID
    silo_id: UUID
    food_id: Optional[UUID]
    remaining_quantity_mg: int
    reserved_quantity_mg: int
    position: int
    status: SiloInventoryBatchStatus
    received_at: datetime
    created_by_operator_id: str
    created_at: datetime
    updated_at: datetime
    food_name: Optional[str] = None
    food_code: Optional[str] = None
    food_provider: Optional[str] = None

    @property
    def remaining_quantity_kg(self) -> float:
        return self.remaining_quantity_mg / 1_000_000

    @property
    def reserved_quantity_kg(self) -> float:
        return self.reserved_quantity_mg / 1_000_000

    @property
    def available_quantity_mg(self) -> int:
        return max(self.remaining_quantity_mg - self.reserved_quantity_mg, 0)

    @property
    def available_quantity_kg(self) -> float:
        return self.available_quantity_mg / 1_000_000


@dataclass(frozen=True)
class SiloStockSummary:
    total_stock_mg: int
    reserved_stock_mg: int

    @property
    def total_stock_kg(self) -> float:
        return self.total_stock_mg / 1_000_000

    @property
    def reserved_stock_kg(self) -> float:
        return self.reserved_stock_mg / 1_000_000

    @property
    def available_stock_mg(self) -> int:
        return max(self.total_stock_mg - self.reserved_stock_mg, 0)

    @property
    def available_stock_kg(self) -> float:
        return self.available_stock_mg / 1_000_000
