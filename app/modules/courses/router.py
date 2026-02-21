from fastapi import APIRouter
router = APIRouter()

@router.get("")
async def list_courses():
    return {"module": "courses", "status": "ready"}
