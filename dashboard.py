from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .auth.utils import get_current_user
from backend.database import get_db
from backend.models.equipment import Equipment
from backend.models.threat import Threat
from backend.models.troop import Troop

router = APIRouter(tags=["dashboard"])


class DashboardStats(BaseModel):
    activeAlerts: int
    threatLevel: str
    deployedUnits: int
    equipmentReady: int


@router.get("/dashboard/stats", response_model=DashboardStats)
def read_dashboard_stats(db: Session = Depends(get_db) , user = Depends(get_current_user) ):
    active_alerts = db.query(Threat).filter(Threat.status != "resolved").count()
    active_threats = db.query(Threat).filter(Threat.status != "resolved").all()
    if any(threat.severity == "CRITICAL" for threat in active_threats):
        threat_level = "CRITICAL"
    elif any(threat.severity == "HIGH" for threat in active_threats):
        threat_level = "HIGH"
    elif any(threat.severity == "MEDIUM" for threat in active_threats):
        threat_level = "MEDIUM"
    else:
        threat_level = "LOW"

    deployed_units = db.query(Troop).count()
    equipment_total = db.query(Equipment).count()
    equipment_ready = db.query(Equipment).filter(Equipment.health_status == "Operational").count()
    equipment_ready_percent = int((equipment_ready / equipment_total) * 100) if equipment_total else 0

    return {
        "activeAlerts": active_alerts,
        "threatLevel": threat_level,
        "deployedUnits": deployed_units,
        "equipmentReady": equipment_ready_percent,
    }
