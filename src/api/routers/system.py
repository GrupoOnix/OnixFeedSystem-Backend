from fastapi import APIRouter

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/status")
async def get_system_status():
    return {"status": "ok"}