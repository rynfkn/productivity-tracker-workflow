from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.activity import ActivityCreate, ActivityResponse, ActivityUpdate, HabitProgressItem, ProgressSummaryResponse
from app.services import activity_service

router = APIRouter(prefix="/api", tags=["activities"])


@router.get("/activities", response_model=list[ActivityResponse])
def get_activities(db: Session = Depends(get_db)):
    return activity_service.get_all_activities(db)


@router.post("/activities", response_model=ActivityResponse)
def create_activity(payload: ActivityCreate, db: Session = Depends(get_db)):
    return activity_service.create_new_activity(db, payload)


@router.patch("/activities/{activity_id}", response_model=ActivityResponse)
def update_activity(activity_id: UUID, payload: ActivityUpdate, db: Session = Depends(get_db)):
    item = activity_service.update_existing_activity(db, activity_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Activity not found")
    return item


@router.delete("/activities/{activity_id}", status_code=204)
def delete_activity(activity_id: UUID, db: Session = Depends(get_db)):
    deleted = activity_service.delete_activity(db, activity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Activity not found")


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


@router.get("/habits/progress", response_model=list[HabitProgressItem])
def get_habit_progress(db: Session = Depends(get_db)):
    return activity_service.get_habit_progress(db)