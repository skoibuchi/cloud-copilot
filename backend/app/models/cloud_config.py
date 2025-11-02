from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class CloudConfig(Base):
    __tablename__ = "cloud_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    provider = Column(String)
    account_name = Column(String)
    region = Column(String, nullable=True)
    # encrypted JSON string of credentials
    credentials = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_onupdate=func.now())

    user = relationship("User", back_populates="cloud_configs")
