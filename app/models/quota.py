from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date
from app.database import Base


class DailyQuota(Base):
    __tablename__ = "daily_quotas"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    date = Column(Date, nullable=False)  # Track by date
    used_quota = Column(Integer, default=0)
    max_quota = Column(Integer, default=5)


class MatchingPool(Base):
    __tablename__ = "matching_pools"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="waiting")  # waiting/matched/cancelled/expired
    entered_at = Column(DateTime, server_default="current_timestamp")
    matched_at = Column(DateTime, nullable=True)
