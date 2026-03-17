from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)

    # Basic info
    gender = Column(String, nullable=False)  # male/female/other
    age = Column(Integer, nullable=False)
    height = Column(Integer, nullable=True)  # cm
    weight = Column(Integer, nullable=True)  # kg

    # Detailed info (stored as JSON)
    personality = Column(JSON, nullable=True)  # {"trait1": "value1", ...}
    hobbies = Column(JSON, nullable=True)  # ["hobby1", "hobby2", ...]
    industry = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    speaking_style = Column(String, nullable=True)
    description = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
