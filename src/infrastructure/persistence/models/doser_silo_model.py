from uuid import UUID

from sqlmodel import Field, SQLModel


class DoserSiloModel(SQLModel, table=True):
    __tablename__ = "doser_silos"

    doser_id: UUID = Field(
        foreign_key="dosers.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    silo_id: UUID = Field(
        foreign_key="silos.id",
        primary_key=True,
        ondelete="CASCADE",
    )
