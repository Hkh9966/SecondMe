from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database import Base


class Preference(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Filter preferences
    target_gender = Column(String, nullable=True)  # male/female/any
    age_range_min = Column(Integer, default=18)
    age_range_max = Column(Integer, default=50)
    height_range_min = Column(Integer, nullable=True)
    height_range_max = Column(Integer, nullable=True)

    # Interest filters
    industries = Column(JSON, nullable=True)  # ["tech", "finance", ...]
    hobbies = Column(JSON, nullable=True)  # ["reading", "gaming", ...]

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class MatchThreshold(Base):
    __tablename__ = "match_thresholds"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    min_heart_score = Column(Integer, default=60)  # Default threshold 60

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
