from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import User, Agent, Preference
from app.schemas import AgentCreate, AgentUpdate, AgentResponse, AgentDiscoverResponse
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/create", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if user already has an agent
    result = await db.execute(select(Agent).where(Agent.user_id == current_user.id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already has an agent")

    # Create agent
    agent = Agent(**agent_data.model_dump(), user_id=current_user.id)
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    return AgentResponse.model_validate(agent)


@router.get("/my", response_model=AgentResponse)
async def get_my_agent(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Agent).where(Agent.user_id == current_user.id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentResponse.model_validate(agent)


@router.put("/update", response_model=AgentResponse)
async def update_agent(
    agent_data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Agent).where(Agent.user_id == current_user.id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Update fields
    for field, value in agent_data.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)

    await db.commit()
    await db.refresh(agent)

    return AgentResponse.model_validate(agent)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentResponse.model_validate(agent)


@router.get("/discover", response_model=AgentDiscoverResponse)
async def discover_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get user's preference
    result = await db.execute(select(Preference).where(Preference.user_id == current_user.id))
    preference = result.scalar_one_or_none()

    # Get current user's agent
    result = await db.execute(select(Agent).where(Agent.user_id == current_user.id))
    current_agent = result.scalar_one_or_none()

    if not current_agent:
        raise HTTPException(status_code=400, detail="You need to create an agent first")

    # Build query
    query = select(Agent).where(Agent.user_id != current_user.id)

    if preference:
        if preference.target_gender and preference.target_gender != "any":
            query = query.where(Agent.gender == preference.target_gender)
        if preference.age_range_min:
            query = query.where(Agent.age >= preference.age_range_min)
        if preference.age_range_max:
            query = query.where(Agent.age <= preference.age_range_max)
        if preference.height_range_min:
            query = query.where(Agent.height >= preference.height_range_min)
        if preference.height_range_max:
            query = query.where(Agent.height <= preference.height_range_max)

    result = await db.execute(query)
    agents = result.scalars().all()

    # Filter by interests if preference has hobbies/industries
    if preference and preference.hobbies:
        agents = [
            a for a in agents
            if a.hobbies and any(h in preference.hobbies for h in a.hobbies)
        ]

    if preference and preference.industries:
        agents = [
            a for a in agents
            if a.industry and a.industry in preference.industries
        ]

    return AgentDiscoverResponse(
        agents=[AgentResponse.model_validate(a) for a in agents],
        total=len(agents)
    )
