from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.activity import ActivityCreate, ActivityResponse
from app.services import activity_service

router = APIRouter(prefix="/api", tags=["activities"])


@router.get("/activities", response_model=list[ActivityResponse])
def get_activities(db: Session = Depends(get_db)):
    return activity_service.get_all_activities(db)


@router.post("/activities", response_model=ActivityResponse)
def create_activity(payload: ActivityCreate, db: Session = Depends(get_db)):
    return activity_service.create_new_activity(db, payload)