from typing import Annotated, Union

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import CheckScheduleUseCaseDep, get_get_system_config_use_case, get_update_system_config_use_case
from api.models.feeding_models import CyclicFeedingRequest, ManualFeedingRequest
from api.models.system_config_models import ScheduleCheckResponse, SystemConfigResponse, UpdateSystemConfigRequest
from application.use_cases.system_config import GetSystemConfigUseCase, UpdateSystemConfigUseCase

router = APIRouter(prefix="/system/config", tags=["System Config"])


@router.get("", response_model=SystemConfigResponse)
async def get_system_config(
    use_case: Annotated[GetSystemConfigUseCase, Depends(get_get_system_config_use_case)],
) -> SystemConfigResponse:
    try:
        return await use_case.execute()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("", response_model=SystemConfigResponse)
async def update_system_config(
    request: UpdateSystemConfigRequest,
    use_case: Annotated[UpdateSystemConfigUseCase, Depends(get_update_system_config_use_case)],
) -> SystemConfigResponse:
    try:
        return await use_case.execute(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/schedule-check", response_model=ScheduleCheckResponse)
async def check_schedule(
    request: Union[ManualFeedingRequest, CyclicFeedingRequest],
    use_case: CheckScheduleUseCaseDep,
) -> ScheduleCheckResponse:
    try:
        return await use_case.execute(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
