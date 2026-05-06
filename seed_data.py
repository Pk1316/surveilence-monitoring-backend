import random
from datetime import datetime, timedelta
from database import engine, SessionLocal, Base
from models.threat import Threat
from models.troop import Troop
from models.equipment import Equipment

THREAT_TYPES = ["Intrusion", "Sabotage", "Insider Threat", "Drone", "Cyber Assault"]
THREAT_ZONES = ["North Sector", "East Sector", "South Sector", "West Sector", "Central Hub"]
THREAT_SEVERITIES = ["Low", "Medium", "High", "Critical"]
THREAT_STATUSES = ["new", "investigating", "mitigated", "resolved"]

TROOP_NAMES = [f"Unit {i:02d}" for i in range(1, 51)]
TROOP_ZONES = ["North", "East", "South", "West", "Central"]
TROOP_STATUS = ["Active", "Standby", "Deployed", "Resupply"]
COMMANDERS = ["Adams", "Baker", "Carter", "Diaz", "Evans", "Ford", "Garcia", "Hall", "Ibrahim", "Jones"]

EQUIPMENT_NAMES = [
    "Armored Vehicle", "Radar Array", "Radio Set", "First Aid Kit",
    "Drone Battery", "Night Vision Goggles", "Comm Tower",
    "Generator", "Tactical Laptop", "Fuel Tank"
]
EQUIPMENT_CATEGORIES = ["Vehicle", "Electronics", "Medical", "Communications", "Support"]
EQUIPMENT_HEALTH = ["Good", "Fair", "Needs Repair", "Critical"]
LOCATIONS = ["Warehouse A", "Forward Base", "Hangar 3", "Command Center", "Supply Depot"]


def seed_threats(session):
    threats = []
    now = datetime.utcnow()
    for i in range(100):
        timestamp = now - timedelta(hours=random.randint(1, 240))
        resolved_at = timestamp + timedelta(hours=random.randint(1, 72)) if random.random() < 0.4 else None
        threats.append(
            Threat(
                type=random.choice(THREAT_TYPES),
                zone=random.choice(THREAT_ZONES),
                severity=random.choice(THREAT_SEVERITIES),
                status=random.choice(THREAT_STATUSES),
                description=f"Detected {random.choice(THREAT_TYPES).lower()} activity in {random.choice(THREAT_ZONES)}.",
                location=random.choice(LOCATIONS),
                timestamp=timestamp,
                resolved_at=resolved_at,
                created_at=timestamp,
                updated_at=timestamp,
            )
        )
    session.add_all(threats)


def seed_troops(session):
    troops = []
    for i in range(100):
        last_deployment = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        troops.append(
            Troop(
                unit_name=random.choice(TROOP_NAMES),
                assigned_zone=random.choice(TROOP_ZONES),
                status=random.choice(TROOP_STATUS),
                personnel_count=random.randint(10, 150),
                commander=f"Lt. {random.choice(COMMANDERS)}",
                contact_info=f"+1-555-{random.randint(1000,9999)}",
                last_deployment=last_deployment,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
    session.add_all(troops)


def seed_equipment(session):
    equipment = []
    now = datetime.utcnow()
    for i in range(100):
        last_maintenance = now - timedelta(days=random.randint(1, 180))
        next_maintenance = last_maintenance + timedelta(days=random.randint(30, 120))
        equipment.append(
            Equipment(
                item_name=random.choice(EQUIPMENT_NAMES),
                quantity=random.randint(1, 50),
                health_status=random.choice(EQUIPMENT_HEALTH),
                category=random.choice(EQUIPMENT_CATEGORIES),
                last_maintenance=last_maintenance,
                next_maintenance=next_maintenance,
                location=random.choice(LOCATIONS),
                created_at=now,
                updated_at=now,
            )
        )
    session.add_all(equipment)


def main():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        seed_threats(session)
        seed_troops(session)
        seed_equipment(session)
        session.commit()
        print("Seed data inserted: 100 threats, 100 troops, 100 equipment records")
    except Exception as error:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()