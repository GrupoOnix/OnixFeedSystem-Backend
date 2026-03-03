"""Repositorio de persistencia para User."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.aggregates.user import User
from domain.repositories import IUserRepository
from domain.value_objects import UserId
from infrastructure.persistence.models.user_model import UserModel


class UserRepository(IUserRepository):
    """Implementación del repositorio de usuarios con SQLModel."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, user: User) -> None:
        """Guarda un nuevo usuario."""
        model = UserModel.from_domain(user)
        self._session.add(model)
        await self._session.flush()

    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        """Busca un usuario por su ID."""
        result = await self._session.get(UserModel, user_id.value)
        return result.to_domain() if result else None

    async def find_by_username(self, username: str) -> Optional[User]:
        """Busca un usuario por su username."""
        stmt = select(UserModel).where(UserModel.username == username.strip().lower())
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_all_user_ids(self) -> List[UserId]:
        """Obtiene los IDs de todos los usuarios registrados."""
        stmt = select(UserModel.id)
        result = await self._session.execute(stmt)
        return [UserId.from_string(str(row[0])) for row in result.all()]
