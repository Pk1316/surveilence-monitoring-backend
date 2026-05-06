from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    health_status = Column(String(50), nullable=False)
    category = Column(String(100))
    last_maintenance = Column(DateTime)
    next_maintenance = Column(DateTime)
    location = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Equipment(id={self.id}, item_name={self.item_name}, quantity={self.quantity})>"
