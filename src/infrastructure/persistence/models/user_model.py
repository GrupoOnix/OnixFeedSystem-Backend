"""Modelo de base de datos para usuarios del sistema."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from domain.aggregates.user import User, UserRole
from domain.value_objects.identifiers import UserId


class UserModel(SQLModel, table=True):
    """Modelo SQLModel para usuarios del sistema."""

    __tablename__ = "users"

    id: UUID = Field(primary_key=True)
    username: str = Field(unique=True, max_length=100, index=True)
    full_name: str = Field(max_length=255)
    hashed_password: str = Field(max_length=255)
    role: str = Field(max_length=20, default=UserRole.USER.value)
    is_superadmin: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

    @staticmethod
    def from_domain(user: User) -> "UserModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return UserModel(
            id=user.id.value,
            username=user.username,
            full_name=user.full_name,
            hashed_password=user.hashed_password,
            role=user.role.value,
            is_superadmin=user.is_superadmin,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def to_domain(self) -> User:
        """Convierte modelo de persistencia a entidad de dominio."""
        return User.reconstruct(
            user_id=UserId(self.id),
            username=self.username,
            full_name=self.full_name,
            hashed_password=self.hashed_password,
            role=UserRole(self.role),
            is_superadmin=self.is_superadmin,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
