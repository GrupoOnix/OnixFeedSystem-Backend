"""Router para gestión de usuarios."""

from fastapi import APIRouter, HTTPException, status

from api.dependencies import (
    CurrentAdminUserDep,
    CurrentSuperAdminUserDep,
    ListUsersUseCaseDep,
    RegisterUserUseCaseDep,
    ResetUserPasswordUseCaseDep,
    UpdateUserRoleUseCaseDep,
    UpdateUserStatusUseCaseDep,
)
from api.models.auth_models import UserResponseModel
from api.models.user_models import (
    ListUsersResponseModel,
    RegisterUserRequestModel,
    ResetPasswordRequestModel,
    UpdateUserRoleRequestModel,
    UpdateUserStatusRequestModel,
)
from application.dtos.auth_dtos import (
    RegisterUserRequest,
    ResetPasswordRequest,
    UpdateUserRoleRequest,
    UpdateUserStatusRequest,
)
from domain.exceptions import (
    InsufficientPermissionsError,
    UserAlreadyExistsError,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserResponseModel,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    request: RegisterUserRequestModel,
    current_user: CurrentAdminUserDep,
    use_case: RegisterUserUseCaseDep,
) -> UserResponseModel:
    """Crea un nuevo usuario. Requiere admin o superadmin."""
    try:
        dto = RegisterUserRequest(
            username=request.username,
            full_name=request.full_name,
            password=request.password,
            role=request.role,
        )
        result = await use_case.execute(
            request=dto,
            creator_is_superadmin=current_user.is_superadmin,
        )
        return UserResponseModel.from_dto(result)
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except InsufficientPermissionsError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )


@router.get("", response_model=ListUsersResponseModel)
async def list_users(
    current_user: CurrentAdminUserDep,
    use_case: ListUsersUseCaseDep,
) -> ListUsersResponseModel:
    """Lista todos los usuarios. Requiere admin o superadmin."""
    result = await use_case.execute()
    return ListUsersResponseModel.from_dto(result)


@router.patch("/{user_id}/status", response_model=UserResponseModel)
async def update_user_status(
    user_id: str,
    request: UpdateUserStatusRequestModel,
    current_user: CurrentAdminUserDep,
    use_case: UpdateUserStatusUseCaseDep,
) -> UserResponseModel:
    """Activa o desactiva un usuario."""
    try:
        dto = UpdateUserStatusRequest(is_active=request.is_active)
        result = await use_case.execute(
            user_id=user_id,
            request=dto,
            requester_id=current_user.id,
            requester_is_superadmin=current_user.is_superadmin,
            requester_is_admin=current_user.role == "admin",
        )
        return UserResponseModel.from_dto(result)
    except InsufficientPermissionsError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.patch("/{user_id}/role", response_model=UserResponseModel)
async def update_user_role(
    user_id: str,
    request: UpdateUserRoleRequestModel,
    current_user: CurrentSuperAdminUserDep,
    use_case: UpdateUserRoleUseCaseDep,
) -> UserResponseModel:
    """Cambia el rol de un usuario. Requiere superadmin."""
    try:
        dto = UpdateUserRoleRequest(role=request.role)
        result = await use_case.execute(
            user_id=user_id,
            request=dto,
            requester_id=current_user.id,
            requester_is_superadmin=True,
        )
        return UserResponseModel.from_dto(result)
    except InsufficientPermissionsError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.patch("/{user_id}/password", response_model=UserResponseModel)
async def reset_user_password(
    user_id: str,
    request: ResetPasswordRequestModel,
    current_user: CurrentSuperAdminUserDep,
    use_case: ResetUserPasswordUseCaseDep,
) -> UserResponseModel:
    """Resetea la contraseña de un usuario. Requiere superadmin."""
    try:
        dto = ResetPasswordRequest(new_password=request.new_password)
        result = await use_case.execute(
            user_id=user_id,
            request=dto,
            requester_id=current_user.id,
            requester_is_superadmin=True,
        )
        return UserResponseModel.from_dto(result)
    except InsufficientPermissionsError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
