"""Router para endpoint de feedback."""

from fastapi import APIRouter, HTTPException, status

from api.dependencies import CreateFeedbackUseCaseDep, CurrentUser
from api.models.feedback_models import CreateFeedbackRequestModel
from application.dtos.feedback_dtos import CreateFeedbackRequest

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_feedback(
    request: CreateFeedbackRequestModel,
    use_case: CreateFeedbackUseCaseDep,
    current_user: CurrentUser,
) -> dict:
    """
    Envía un nuevo feedback al sistema.

    - **name**: (Opcional) Nombre del usuario
    - **email**: (Opcional) Email del usuario
    - **type**: Tipo de feedback: 'suggestion', 'bug' o 'general'
    - **message**: Contenido del mensaje
    """
    try:
        dto = CreateFeedbackRequest(
            type=request.type,
            message=request.message,
            name=request.name,
            email=request.email,
        )
        await use_case.execute(dto, user_id=current_user.id)
        return {"message": "Feedback recibido correctamente"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
