from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base

class EventModel(Base):
    """SQLAlchemy model representing security events detected in the video stream."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    tracking_id = Column(String, nullable=True, index=True)
    source_stream = Column(String, nullable=False)
    details = Column(String, nullable=True)  # JSON-formatted string for extra metadata

    # Relationship to alerts
    alerts = relationship("AlertModel", back_populates="event", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, type='{self.event_type}', track_id='{self.tracking_id}')>"


class AlertModel(Base):
    """SQLAlchemy model representing alerts triggered by detected security events."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    alert_type = Column(String, nullable=False, index=True)
    message = Column(String, nullable=False)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=True)
    status = Column(String, default="active", nullable=False)  # active, resolved

    # Relationship to events
    event = relationship("EventModel", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, type='{self.alert_type}', status='{self.status}')>"
