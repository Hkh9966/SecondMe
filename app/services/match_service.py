from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime
from typing import Optional

from app.models import Agent, Preference, MatchingPool, Conversation
from app.config import settings


class MatchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def join_pool(self, agent_id: int, user_id: int) -> MatchingPool:
        """Add agent to matching pool"""
        # Check if already in pool
        result = await self.db.execute(
            select(MatchingPool).where(
                and_(
                    MatchingPool.agent_id == agent_id,
                    MatchingPool.status == "waiting"
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        # Create new pool entry
        pool_entry = MatchingPool(
            agent_id=agent_id,
            user_id=user_id,
            status="waiting"
        )
        self.db.add(pool_entry)
        await self.db.commit()
        await self.db.refresh(pool_entry)

        return pool_entry

    async def find_match(self, agent_id: int, user_id: int) -> Optional[MatchingPool]:
        """Find a match for the agent in the pool"""
        # Get current agent's preferences
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        current_agent = result.scalar_one()

        if not current_agent:
            return None

        # Get user preferences
        result = await self.db.execute(select(Preference).where(Preference.user_id == user_id))
        preference = result.scalar_one_or_none()

        # Build matching query - find other waiting agents
        query = select(MatchingPool).where(
            and_(
                MatchingPool.status == "waiting",
                MatchingPool.agent_id != agent_id,
                MatchingPool.user_id != user_id
            )
        )

        result = await self.db.execute(query)
        pool_entries = result.scalars().all()

        # Filter by preferences
        matched_entry = None
        for entry in pool_entries:
            result = await self.db.execute(select(Agent).where(Agent.id == entry.agent_id))
            other_agent = result.scalar_one_or_none()

            if not other_agent:
                continue

            # Check gender preference
            if preference and preference.target_gender and preference.target_gender != "any":
                if other_agent.gender != preference.target_gender:
                    continue

            # Check age preference
            if preference:
                if preference.age_range_min and other_agent.age < preference.age_range_min:
                    continue
                if preference.age_range_max and other_agent.age > preference.age_range_max:
                    continue

            # Check height preference
            if preference and preference.height_range_min and other_agent.height:
                if other_agent.height < preference.height_range_min:
                    continue
            if preference and preference.height_range_max and other_agent.height:
                if other_agent.height > preference.height_range_max:
                    continue

            # Found a match!
            matched_entry = entry
            break

        return matched_entry

    async def create_conversation(
        self,
        initiator_agent_id: int,
        receiver_agent_id: int,
        initiator_user_id: int,
        receiver_user_id: int
    ) -> Conversation:
        """Create a conversation between two agents"""
        conversation = Conversation(
            initiator_agent_id=initiator_agent_id,
            receiver_agent_id=receiver_agent_id,
            initiator_user_id=initiator_user_id,
            receiver_user_id=receiver_user_id,
            status="running"
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation

    async def update_pool_status(self, pool_id: int, status: str):
        """Update pool entry status"""
        result = await self.db.execute(select(MatchingPool).where(MatchingPool.id == pool_id))
        entry = result.scalar_one_or_none()

        if entry:
            entry.status = status
            if status == "matched":
                entry.matched_at = datetime.utcnow()
            await self.db.commit()

    async def leave_pool(self, agent_id: int) -> bool:
        """Remove agent from pool"""
        result = await self.db.execute(
            select(MatchingPool).where(
                and_(
                    MatchingPool.agent_id == agent_id,
                    MatchingPool.status == "waiting"
                )
            )
        )
        entry = result.scalar_one_or_none()

        if entry:
            entry.status = "cancelled"
            await self.db.commit()
            return True

        return False

    async def get_pool_status(self, agent_id: int) -> Optional[dict]:
        """Get current pool status for an agent"""
        result = await self.db.execute(
            select(MatchingPool).where(
                and_(
                    MatchingPool.agent_id == agent_id,
                    MatchingPool.status == "waiting"
                )
            )
        )
        entry = result.scalar_one_or_none()

        if not entry:
            return None

        return {
            "in_pool": True,
            "status": entry.status,
            "entered_at": entry.entered_at,
            "waiting_time": (datetime.utcnow() - entry.entered_at).seconds
        }
