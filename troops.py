from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .auth.utils import get_current_user
from backend.database import get_db
from backend.models.troop import Troop

router = APIRouter(tags=["troops"])


class TroopCreate(BaseModel):
    unit_name: str
    assigned_zone: str
    personnel_count: int
    status: str = "Active"
    commander: str | None = None
    contact_info: str | None = None
    last_deployment: datetime | None = None


class TroopOut(TroopCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TroopList(BaseModel):
    items: list[TroopOut]
    total: int
    has_more: bool


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


@router.get("/troops", response_model=TroopList)
def read_troops(
    assigned_zone: str = Query("all"),
    status: str = Query("all"),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Troop)

    if assigned_zone != "all":
        query = query.filter(Troop.assigned_zone == assigned_zone)
    if status != "all":
        query = query.filter(Troop.status == status)

    start = parse_date(start_date)
    end = parse_date(end_date)
    if start:
        query = query.filter(Troop.last_deployment >= start)
    if end:
        query = query.filter(Troop.last_deployment <= end)

    total = query.count()
    items = query.order_by(Troop.id.desc()).offset(offset).limit(limit).all()
    has_more = offset + len(items) < total

    return {"items": items, "total": total, "has_more": has_more}


@router.post("/troops", response_model=TroopOut, status_code=201)
def create_troop(payload: TroopCreate, db: Session = Depends(get_db) , user = Depends(get_current_user)):
    troop = Troop(**payload.model_dump())
    db.add(troop)
    db.commit()
    db.refresh(troop)
    return troop
