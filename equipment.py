from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .auth.utils import get_current_user    
from backend.database import get_db
from backend.models.equipment import Equipment

router = APIRouter(tags=["equipment"])


class EquipmentCreate(BaseModel):
    item_name: str
    quantity: int
    health_status: str
    category: str | None = None
    location: str | None = None
    last_maintenance: datetime | None = None


class EquipmentOut(EquipmentCreate):
    id: int
    next_maintenance: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EquipmentList(BaseModel):
    items: list[EquipmentOut]
    total: int
    has_more: bool


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


@router.get("/equipment", response_model=EquipmentList)
def read_equipment(
    category: str = Query("all"),
    health_status: str = Query("all"),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=200),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    query = db.query(Equipment)

    if category != "all":
        query = query.filter(Equipment.category == category)
    if health_status != "all":
        query = query.filter(Equipment.health_status == health_status)

    start = parse_date(start_date)
    end = parse_date(end_date)
    if start:
        query = query.filter(Equipment.last_maintenance >= start)
    if end:
        query = query.filter(Equipment.last_maintenance <= end)

    total = query.count()
    items = query.order_by(Equipment.id.desc()).offset(offset).limit(limit).all()
    has_more = offset + len(items) < total

    return {"items": items, "total": total, "has_more": has_more}


@router.post("/equipment", response_model=EquipmentOut, status_code=201)
def create_equipment(payload: EquipmentCreate, db: Session = Depends(get_db)):
    equipment = Equipment(**payload.model_dump())
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment
