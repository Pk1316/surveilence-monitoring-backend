from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .auth.utils import get_current_user
from backend.database import get_db
from backend.models.threat import Threat
router = APIRouter(tags=["threats"])


class ThreatOut(BaseModel):
    id: int
    type: str
    zone: str
    severity: str
    status: str
    description: str | None = None
    location: str | None = None
    timestamp: datetime
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ThreatList(BaseModel):
    items: list[ThreatOut]
    total: int
    has_more: bool


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


@router.get("/threats", response_model=ThreatList)
def read_threats(
    severity: str = Query("all"),
    status: str = Query("all"),
    zone: str = Query("all"),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=200),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    query = db.query(Threat)

    if severity != "all":
        query = query.filter(Threat.severity == severity)
    if status != "all":
        query = query.filter(Threat.status == status)
    if zone != "all":
        query = query.filter(Threat.zone == zone)

    start = parse_date(start_date)
    end = parse_date(end_date)
    if start:
        query = query.filter(Threat.timestamp >= start)
    if end:
        query = query.filter(Threat.timestamp <= end)

    total = query.count()
    items = query.order_by(Threat.timestamp.desc()).offset(offset).limit(limit).all()
    has_more = offset + len(items) < total

    return {"items": items, "total": total, "has_more": has_more}
