from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.activity import ActivityCreate, ActivityResponse, ProgressSummaryResponse
from app.services import activity_service

router = APIRouter(prefix="/api", tags=["activities"])


@router.get("/activities", response_model=list[ActivityResponse])
def get_activities(db: Session = Depends(get_db)):
    return activity_service.get_all_activities(db)


@router.post("/activities", response_model=ActivityResponse)
def create_activity(payload: ActivityCreate, db: Session = Depends(get_db)):
    return activity_service.create_new_activity(db, payload)


@router.get("/progress/today", response_model=ProgressSummaryResponse)
def get_today_progress(db: Session = Depends(get_db)):
    return activity_service.get_today_progress_summary(db)


@router.get("/progress", response_model=ProgressSummaryResponse)
def get_progress(
    from_dt: datetime = Query(alias="from"),
    to_dt: datetime = Query(alias="to"),
    db: Session = Depends(get_db),
):
    if to_dt <= from_dt:
        raise HTTPException(status_code=400, detail="'to' must be greater than 'from'")

    return activity_service.get_progress_summary(db, start=from_dt, end=to_dt)