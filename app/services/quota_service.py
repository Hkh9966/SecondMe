from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date, datetime
from app.models import DailyQuota, Agent
from app.config import settings


class QuotaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_quota(self, agent_id: int) -> tuple[bool, int, int]:
        """Check if agent has quota available. Returns (has_quota, used, max)"""
        today = date.today()

        result = await self.db.execute(
            select(DailyQuota).where(
                and_(
                    DailyQuota.agent_id == agent_id,
                    DailyQuota.date == today
                )
            )
        )
        quota = result.scalar_one_or_none()

        if not quota:
            # Create new quota record
            quota = DailyQuota(
                agent_id=agent_id,
                date=today,
                used_quota=0,
                max_quota=settings.daily_quota_limit
            )
            self.db.add(quota)
            await self.db.commit()
            await self.db.refresh(quota)

        has_quota = quota.used_quota < quota.max_quota
        return has_quota, quota.used_quota, quota.max_quota

    async def use_quota(self, agent_id: int) -> bool:
        """Use one quota for the agent. Returns True if successful"""
        has_quota, used, max_quota = await self.check_quota(agent_id)

        if not has_quota:
            return False

        today = date.today()
        result = await self.db.execute(
            select(DailyQuota).where(
                and_(
                    DailyQuota.agent_id == agent_id,
                    DailyQuota.date == today
                )
            )
        )
        quota = result.scalar_one_or_none()

        if quota:
            quota.used_quota += 1
            await self.db.commit()

        return True

    async def get_quota_status(self, agent_id: int) -> dict:
        """Get current quota status"""
        has_quota, used, max_quota = await self.check_quota(agent_id)
        return {
            "has_quota": has_quota,
            "used": used,
            "max": max_quota,
            "remaining": max_quota - used
        }
