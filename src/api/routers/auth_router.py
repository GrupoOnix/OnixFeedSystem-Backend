"""Router para endpoints de autenticación."""

from fastapi import APIRouter, HTTPException, status

from api.dependencies import CurrentUser, LoginUseCaseDep, RegisterUserUseCaseDep
from api.models.auth_models import LoginRequest, LoginResponse, RegisterRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    use_case: RegisterUserUseCaseDep,
) -> UserResponse:
    """
    Registra un nuevo usuario en el sistema.

    - **username**: Nombre de usuario (único)
    - **password**: Contraseña (mínimo 6 caracteres)
    - **name**: Nombre completo
    - **role**: Rol del usuario (admin, operator, viewer)
    - **email**: Email (opcional)
    """
    try:
        user = await use_case.execute(
            username=request.username,
            password=request.password,
            name=request.name,
            role=request.role,
            email=request.email,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return UserResponse(
        id=str(user.id),
        username=user.username,
        name=user.name,
        role=user.role,
        email=user.email,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    use_case: LoginUseCaseDep,
) -> LoginResponse:
    """
    Autentica un usuario y retorna un JWT token.

    - **username**: Nombre de usuario
    - **password**: Contraseña
    """
    result = await use_case.execute(
        username=request.username,
        password=request.password,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    return LoginResponse(
        access_token=result.access_token,
        token_type="bearer",
        user=UserResponse(
            id=str(result.user.id),
            username=result.user.username,
            name=result.user.name,
            role=result.user.role,
            email=result.user.email,
        ),
        expires_in=result.expires_in,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: CurrentUser,
) -> UserResponse:
    """
    Retorna los datos del usuario autenticado.

    Requiere un token JWT válido en el header Authorization.
    """
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        name=current_user.name,
        role=current_user.role,
        email=current_user.email,
    )
