from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from database import Base


class Threat(Base):
    __tablename__ = "threats"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(100), nullable=False)
    zone = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="new")
    description = Column(Text)
    location = Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Threat(id={self.id}, type={self.type}, severity={self.severity})>"
