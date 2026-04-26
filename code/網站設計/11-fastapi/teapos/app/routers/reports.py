from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from datetime import date

from app.database import get_db
from app.schemas import DailyReport
from app import crud

router = APIRouter(prefix="/api/reports", tags=["reports"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("/daily", response_model=DailyReport)
async def get_daily_report(
    db: DbDep,
    target_date: date | None = Query(default=None),
) -> DailyReport:
    report = await crud.get_daily_report(db, target_date)
    return DailyReport(**report)