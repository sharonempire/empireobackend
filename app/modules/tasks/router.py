from fastapi import APIRouter
router = APIRouter()

@router.get("")
async def list_tasks():
    return {"module": "tasks", "status": "ready", "message": "Full implementation in progress"}
