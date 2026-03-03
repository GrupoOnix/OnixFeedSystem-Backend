"""Modelo de persistencia para User."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from domain.aggregates.user import User
from domain.value_objects import UserId


class UserModel(SQLModel, table=True):
    """Modelo de persistencia para User."""

    __tablename__ = "users"

    id: UUID = Field(primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    password_hash: str = Field(max_length=128)
    password_salt: str = Field(max_length=64)
    name: str = Field(max_length=100)
    role: str = Field(default="admin", max_length=20)
    email: Optional[str] = Field(default=None, max_length=200)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

    @staticmethod
    def from_domain(user: User) -> "UserModel":
        """Convierte entidad de dominio a modelo de persistencia."""
        return UserModel(
            id=user.id.value,
            username=user.username,
            password_hash=user.password_hash,
            password_salt=user.password_salt,
            name=user.name,
            role=user.role,
            email=user.email,
            created_at=user.created_at,
        )

    def to_domain(self) -> User:
        """Convierte modelo de persistencia a entidad de dominio."""
        user = User(
            username=self.username,
            password_hash=self.password_hash,
            password_salt=self.password_salt,
            name=self.name,
            role=self.role,
            email=self.email,
        )
        user._set_id(UserId(self.id))
        user._set_created_at(self.created_at)
        return user
