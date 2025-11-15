from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from app.database.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
