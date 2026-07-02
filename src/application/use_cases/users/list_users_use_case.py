"""Use case para listar usuarios."""

from application.dtos.auth_dtos import ListUsersResponse, UserResponse
from domain.repositories import IUserRepository


class ListUsersUseCase:
    """Caso de uso para listar todos los usuarios del sistema."""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    async def execute(self) -> ListUsersResponse:
        """Lista todos los usuarios ordenados por username."""
        users = await self.user_repository.list()
        return ListUsersResponse(
            users=[
                UserResponse(
                    id=str(user.id),
                    username=user.username,
                    full_name=user.full_name,
                    role=user.role.value,
                    is_superadmin=user.is_superadmin,
                    is_active=user.is_active,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                )
                for user in users
            ]
        )
