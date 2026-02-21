from fastapi import APIRouter
router = APIRouter()

@router.get("")
async def list_conversations():
    return {"module": "conversations", "status": "ready", "message": "Full implementation in progress"}
