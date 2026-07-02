"""Implementación del repositorio de usuarios."""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from domain.aggregates.user import User
from domain.repositories import IUserRepository
from domain.value_objects.identifiers import UserId
from infrastructure.persistence.models.user_model import UserModel


class UserRepository(IUserRepository):
    """Implementación SQLAlchemy del repositorio de usuarios."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> None:
        """Guarda o actualiza un usuario."""
        existing = await self.session.get(UserModel, user.id.value)

        if existing:
            existing.username = user.username
            existing.full_name = user.full_name
            existing.hashed_password = user.hashed_password
            existing.role = user.role.value
            existing.is_superadmin = user.is_superadmin
            existing.is_active = user.is_active
            existing.updated_at = user.updated_at
        else:
            user_model = UserModel.from_domain(user)
            self.session.add(user_model)

        await self.session.flush()

    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        """Busca un usuario por su ID."""
        user_model = await self.session.get(UserModel, user_id.value)
        return user_model.to_domain() if user_model else None

    async def find_by_username(self, username: str) -> Optional[User]:
        """Busca un usuario por su nombre de usuario (case-insensitive)."""
        result = await self.session.execute(
            select(UserModel).where(func.lower(col(UserModel.username)) == func.lower(username))
        )
        user_model = result.scalar_one_or_none()
        return user_model.to_domain() if user_model else None

    async def list(self) -> List[User]:
        """Lista todos los usuarios ordenados por username."""
        result = await self.session.execute(select(UserModel).order_by(col(UserModel.username)))
        return [model.to_domain() for model in result.scalars().all()]

    async def exists_by_username(self, username: str, exclude_id: Optional[UserId] = None) -> bool:
        """Verifica si existe un usuario con el username dado (case-insensitive)."""
        query = select(UserModel).where(func.lower(col(UserModel.username)) == func.lower(username.strip()))

        if exclude_id:
            query = query.where(col(UserModel.id) != exclude_id.value)

        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
