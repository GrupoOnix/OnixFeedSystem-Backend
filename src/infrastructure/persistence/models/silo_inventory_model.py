from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlmodel import Field, SQLModel


class SiloInventoryBatchModel(SQLModel, table=True):
    __tablename__ = "silo_inventory_batches"
    __table_args__ = (Index("ix_silo_batches_fifo", "silo_id", "status", "position"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    silo_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("silos.id", ondelete="CASCADE"), nullable=False)
    )
    food_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("foods.id", ondelete="RESTRICT"), nullable=True),
    )
    remaining_quantity_mg: int = Field(sa_column=Column(BigInteger, nullable=False))
    position: int = Field(nullable=False)
    status: str = Field(sa_column=Column(String(20), nullable=False))
    received_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    created_by_operator_id: str = Field(sa_column=Column(String, nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class SiloInventoryMovementModel(SQLModel, table=True):
    __tablename__ = "silo_inventory_movements"
    __table_args__ = (Index("ix_silo_inventory_movements_silo_created", "silo_id", "created_at"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    silo_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("silos.id", ondelete="CASCADE"), nullable=False)
    )
    batch_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("silo_inventory_batches.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    movement_type: str = Field(sa_column=Column(String(30), nullable=False))
    operator_id: str = Field(sa_column=Column(String, nullable=False))
    reason: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    quantity_delta_mg: int = Field(sa_column=Column(BigInteger, nullable=False, default=0))
    previous_quantity_mg: int = Field(sa_column=Column(BigInteger, nullable=False))
    new_quantity_mg: int = Field(sa_column=Column(BigInteger, nullable=False))
    previous_food_id: Optional[UUID] = Field(default=None, sa_column=Column(PGUUID(as_uuid=True), nullable=True))
    new_food_id: Optional[UUID] = Field(default=None, sa_column=Column(PGUUID(as_uuid=True), nullable=True))
    previous_position: Optional[int] = None
    new_position: Optional[int] = None
    feeding_session_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String, ForeignKey("feeding_sessions.id", ondelete="SET NULL"), nullable=True),
    )
    cage_feeding_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String, ForeignKey("cage_feedings.id", ondelete="SET NULL"), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class SiloStockReservationModel(SQLModel, table=True):
    __tablename__ = "silo_stock_reservations"
    __table_args__ = (
        Index("ix_silo_reservations_session_status", "feeding_session_id", "status"),
        Index("ix_silo_reservations_batch_status", "batch_id", "status"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    feeding_session_id: str = Field(
        sa_column=Column(String, ForeignKey("feeding_sessions.id", ondelete="CASCADE"), nullable=False)
    )
    silo_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("silos.id", ondelete="CASCADE"), nullable=False)
    )
    batch_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("silo_inventory_batches.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    reserved_quantity_mg: int = Field(sa_column=Column(BigInteger, nullable=False))
    consumed_quantity_mg: int = Field(sa_column=Column(BigInteger, nullable=False, default=0))
    status: str = Field(sa_column=Column(String(20), nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class FeedingBatchConsumptionModel(SQLModel, table=True):
    __tablename__ = "feeding_batch_consumptions"
    __table_args__ = (
        Index("ix_feeding_batch_consumptions_session", "feeding_session_id"),
        Index("ix_feeding_batch_consumptions_batch", "batch_id"),
        Index("ix_feeding_batch_consumptions_food", "food_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    feeding_session_id: str = Field(
        sa_column=Column(String, ForeignKey("feeding_sessions.id", ondelete="CASCADE"), nullable=False)
    )
    cage_feeding_id: str = Field(
        sa_column=Column(String, ForeignKey("cage_feedings.id", ondelete="CASCADE"), nullable=False)
    )
    silo_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("silos.id", ondelete="RESTRICT"), nullable=False)
    )
    batch_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("silo_inventory_batches.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    food_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("foods.id", ondelete="RESTRICT"), nullable=False)
    )
    quantity_mg: int = Field(sa_column=Column(BigInteger, nullable=False))
    operator_id: str = Field(sa_column=Column(String, nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
