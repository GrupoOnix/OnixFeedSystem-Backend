"""Router para autenticación."""

from fastapi import APIRouter, HTTPException, status

from api.dependencies import (
    AuthenticateUserUseCaseDep,
    ChangePasswordUseCaseDep,
    CurrentUserForPasswordChangeDep,
    CurrentUserReadDep,
)
from api.models.auth_models import (
    ChangePasswordRequestModel,
    LoginRequestModel,
    LoginResponseModel,
    UserResponseModel,
)
from application.dtos.auth_dtos import ChangePasswordRequest, LoginRequest
from domain.exceptions import InvalidCredentialsError, UserInactiveError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
async def login(
    request: LoginRequestModel,
    use_case: AuthenticateUserUseCaseDep,
) -> LoginResponseModel:
    """
    Inicia sesión con username y password.

    Devuelve un JWT de acceso válido por 2 horas.
    """
    try:
        dto = LoginRequest(
            username=request.username,
            password=request.password,
        )
        result = await use_case.execute(dto)
        return LoginResponseModel.from_dto(result)
    except (InvalidCredentialsError, UserInactiveError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponseModel)
async def get_current_user(current_user: CurrentUserReadDep) -> UserResponseModel:
    """Devuelve los datos del usuario autenticado."""
    return UserResponseModel.from_dto(current_user)


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: ChangePasswordRequestModel,
    current_user: CurrentUserForPasswordChangeDep,
    use_case: ChangePasswordUseCaseDep,
) -> None:
    """Cambia la contraseña del usuario autenticado."""
    try:
        dto = ChangePasswordRequest(
            current_password=request.current_password,
            new_password=request.new_password,
        )
        await use_case.execute(
            user_id=current_user.id,
            request=dto,
        )
    except (InvalidCredentialsError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
