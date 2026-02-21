from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from app.database import get_db
from app.dependencies import get_current_user
from app.modules.events.service import EventService
from app.modules.events.schemas import EventOut

router = APIRouter()


@router.get("/timeline/{entity_type}/{entity_id}", response_model=List[EventOut])
async def get_timeline(entity_type: str, entity_id: UUID, limit: int = Query(50),
                       offset: int = Query(0), db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await EventService(db).get_timeline(entity_type, entity_id, limit, offset)


@router.get("/type/{event_type}", response_model=List[EventOut])
async def get_by_type(event_type: str, limit: int = Query(50),
                      db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await EventService(db).get_by_type(event_type, limit)
