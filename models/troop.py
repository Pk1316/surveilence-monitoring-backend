from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base


class Troop(Base):
    __tablename__ = "troops"

    id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String(100), nullable=False)
    assigned_zone = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="Active")
    personnel_count = Column(Integer, nullable=False)
    commander = Column(String(255))
    contact_info = Column(String(255))
    last_deployment = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Troop(id={self.id}, unit_name={self.unit_name}, zone={self.assigned_zone})>"
