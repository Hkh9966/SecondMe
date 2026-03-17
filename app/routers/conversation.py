from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import List
import asyncio
import logging

from app.database import get_db
from app.models import User, Agent, Conversation, Message, MatchingPool, Preference, MatchThreshold
from app.schemas import (
    ConversationResponse, ConversationDetailResponse, MessageResponse,
    PoolStatusResponse, JoinPoolResponse, EscalateResponse, HeartScoreResponse
)
from app.routers.auth import get_current_user
from app.services.quota_service import QuotaService
from app.services.match_service import MatchService
from app.services.heart_score_service import HeartScoreService
from app.agents.base import SecondMeAgent
from app.agents.a2a import A2AMessage, MessageType
from app.agents.tools import calculate_heart_score
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/conversation", tags=["conversation"])


@router.post("/join-pool", response_model=JoinPoolResponse)
async def join_pool(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Join the matching pool"""
    # Get user's agent
    result = await db.execute(select(Agent).where(Agent.user_id == current_user.id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=400, detail="You need to create an agent first")

    # Check quota
    quota_service = QuotaService(db)
    has_quota, used, max_quota = await quota_service.check_quota(agent.id)

    if not has_quota:
        raise HTTPException(
            status_code=400,
            detail=f"Daily quota exhausted. Used: {used}/{max_quota}"
        )

    # Use quota
    await quota_service.use_quota(agent.id)

    # Join pool
    match_service = MatchService(db)
    pool_entry = await match_service.join_pool(agent.id, current_user.id)

    # Try to find a match immediately
    matched_entry = await match_service.find_match(agent.id, current_user.id)

    if matched_entry:
        # Get both agents
        result = await db.execute(select(Agent).where(Agent.id == agent.id))
        initiator_agent = result.scalar_one()

        result = await db.execute(select(Agent).where(Agent.id == matched_entry.agent_id))
        receiver_agent = result.scalar_one()

        # Update pool status
        await match_service.update_pool_status(pool_entry.id, "matched")
        await match_service.update_pool_status(matched_entry.id, "matched")

        # Create conversation
        conversation = await match_service.create_conversation(
            initiator_agent_id=agent.id,
            receiver_agent_id=receiver_agent.id,
            initiator_user_id=current_user.id,
            receiver_user_id=matched_entry.user_id
        )

        # Start the conversation asynchronously
        asyncio.create_task(run_conversation(conversation.id, db))

        return JoinPoolResponse(
            success=True,
            message="Match found! Conversation started.",
            pool_entry_id=pool_entry.id
        )

    return JoinPoolResponse(
        success=True,
        message="Added to pool. Waiting for a match...",
        pool_entry_id=pool_entry.id
    )


@router.get("/pool-status", response_model=PoolStatusResponse)
async def get_pool_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current pool status"""
    result = await db.execute(select(Agent).where(Agent.user_id == current_user.id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=400, detail="You need to create an agent first")

    match_service = MatchService(db)
    pool_status = await match_service.get_pool_status(agent.id)

    if not pool_status:
        return PoolStatusResponse(in_pool=False)

    # Check if matched conversation exists
    matched_conversation_id = None
    result = await db.execute(
        select(Conversation).where(
            (Conversation.initiator_agent_id == agent.id) |
            (Conversation.receiver_agent_id == agent.id)
        )
    )
    conversations = result.scalars().all()
    for conv in conversations:
        if conv.status in ["running", "completed"]:
            matched_conversation_id = conv.id

    return PoolStatusResponse(
        in_pool=True,
        status=pool_status["status"],
        matched_conversation_id=matched_conversation_id,
        waiting_time=pool_status.get("waiting_time")
    )


@router.post("/leave-pool")
async def leave_pool(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Leave the matching pool"""
    result = await db.execute(select(Agent).where(Agent.user_id == current_user.id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=400, detail="You need to create an agent first")

    match_service = MatchService(db)
    success = await match_service.leave_pool(agent.id)

    if not success:
        raise HTTPException(status_code=400, detail="Not in pool")

    return {"success": True, "message": "Left the pool"}


@router.get("/my", response_model=List[ConversationResponse])
async def get_my_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all conversations for the current user"""
    result = await db.execute(
        select(Conversation).where(
            (Conversation.initiator_user_id == current_user.id) |
            (Conversation.receiver_user_id == current_user.id)
        )
    )
    conversations = result.scalars().all()

    return [ConversationResponse.model_validate(c) for c in conversations]


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation details with messages"""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            (Conversation.initiator_user_id == current_user.id) |
            (Conversation.receiver_user_id == current_user.id)
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get messages
    result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id)
    )
    messages = result.scalars().all()

    return ConversationDetailResponse(
        **ConversationResponse.model_validate(conversation).model_dump(),
        messages=[MessageResponse.model_validate(m) for m in messages]
    )


@router.post("/{conversation_id}/escalate", response_model=EscalateResponse)
async def escalate_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Escalate to real user conversation (if heart score threshold met)"""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            (Conversation.initiator_user_id == current_user.id) |
            (Conversation.receiver_user_id == current_user.id)
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.status not in ["completed", "matched"]:
        raise HTTPException(status_code=400, detail="Conversation not completed yet")

    # Check heart score threshold
    initiator_threshold_result = await db.execute(
        select(MatchThreshold).where(MatchThreshold.user_id == conversation.initiator_user_id)
    )
    initiator_threshold = initiator_threshold_result.scalar_one_or_none()

    receiver_threshold_result = await db.execute(
        select(MatchThreshold).where(MatchThreshold.user_id == conversation.receiver_user_id)
    )
    receiver_threshold = receiver_threshold_result.scalar_one_or_none()

    initiator_threshold_value = initiator_threshold.min_heart_score if initiator_threshold else 60
    receiver_threshold_value = receiver_threshold.min_heart_score if receiver_threshold else 60

    # Check if both thresholds are met
    if (conversation.heart_score_initiator or 0) >= initiator_threshold_value and \
       (conversation.heart_score_receiver or 0) >= receiver_threshold_value:

        conversation.status = "escalated"
        await db.commit()

        return EscalateResponse(
            success=True,
            message="Conversation escalated to real user interaction!"
        )

    return EscalateResponse(
        success=False,
        message="Heart score threshold not met for both users."
    )


@router.get("/{conversation_id}/heart-score", response_model=HeartScoreResponse)
async def get_heart_score(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get heart score analysis for a conversation"""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            (Conversation.initiator_user_id == current_user.id) |
            (Conversation.receiver_user_id == current_user.id)
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get agents
    result = await db.execute(select(Agent).where(Agent.id == conversation.initiator_agent_id))
    initiator_agent = result.scalar_one()

    result = await db.execute(select(Agent).where(Agent.id == conversation.receiver_agent_id))
    receiver_agent = result.scalar_one()

    # Get messages
    result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id)
    )
    messages = result.scalars().all()

    # Calculate heart scores if not already calculated
    heart_score_service = HeartScoreService()

    initiator_score = None
    receiver_score = None

    if conversation.heart_score_initiator is None:
        initiator_result = await heart_score_service.calculate_heart_score(
            initiator_agent, receiver_agent, conversation, messages
        )
        initiator_score = initiator_result["total_score"]
        conversation.heart_score_initiator = initiator_score
    else:
        initiator_score = conversation.heart_score_initiator
        initiator_result = {"total_score": initiator_score}

    if conversation.heart_score_receiver is None:
        receiver_result = await heart_score_service.calculate_heart_score(
            receiver_agent, initiator_agent, conversation, messages
        )
        receiver_score = receiver_result["total_score"]
        conversation.heart_score_receiver = receiver_score
    else:
        receiver_score = conversation.heart_score_receiver
        receiver_result = {"total_score": receiver_score}

    # Get thresholds
    initiator_threshold_result = await db.execute(
        select(MatchThreshold).where(MatchThreshold.user_id == conversation.initiator_user_id)
    )
    initiator_threshold = initiator_threshold_result.scalar_one_or_none()

    receiver_threshold_result = await db.execute(
        select(MatchThreshold).where(MatchThreshold.user_id == conversation.receiver_user_id)
    )
    receiver_threshold = receiver_threshold_result.scalar_one_or_none()

    both_match_threshold = (
        initiator_score >= (initiator_threshold.min_heart_score if initiator_threshold else 60) and
        receiver_score >= (receiver_threshold.min_heart_score if receiver_threshold else 60)
    )

    await db.commit()

    return HeartScoreResponse(
        conversation_id=conversation_id,
        initiator_heart_score=int(initiator_score),
        receiver_heart_score=int(receiver_score),
        both_match_threshold=both_match_threshold,
        can_escalate=both_match_threshold,
        details={
            "initiator": initiator_result,
            "receiver": receiver_result
        }
    )


async def run_conversation(conversation_id: int, db: AsyncSession):
    """
    Background task to run the agent conversation using ADK-style Agent
    特点:
    - 每个Agent有独立的记忆系统
    - 使用A2A协议进行通信
    - 基于用户画像生成个性化回复
    - 对话结束后计算心动值并存入记忆
    """
    logger.info(f"Starting ADK conversation {conversation_id}")

    # Get conversation
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalar_one()

    # Get agents
    result = await db.execute(select(Agent).where(Agent.id == conversation.initiator_agent_id))
    initiator_agent = result.scalar_one()

    result = await db.execute(select(Agent).where(Agent.id == conversation.receiver_agent_id))
    receiver_agent = result.scalar_one()

    # Build agent profiles
    initiator_profile = {
        "name": initiator_agent.name,
        "age": initiator_agent.age,
        "gender": initiator_agent.gender,
        "height": initiator_agent.height,
        "weight": initiator_agent.weight,
        "industry": initiator_agent.industry,
        "job_title": initiator_agent.job_title,
        "hobbies": initiator_agent.hobbies or [],
        "personality": initiator_agent.personality or {},
        "speaking_style": initiator_agent.speaking_style or "friendly and natural",
        "description": initiator_agent.description or "",
    }

    receiver_profile = {
        "name": receiver_agent.name,
        "age": receiver_agent.age,
        "gender": receiver_agent.gender,
        "height": receiver_agent.height,
        "weight": receiver_agent.weight,
        "industry": receiver_agent.industry,
        "job_title": receiver_agent.job_title,
        "hobbies": receiver_agent.hobbies or [],
        "personality": receiver_agent.personality or {},
        "speaking_style": receiver_agent.speaking_style or "friendly and natural",
        "description": receiver_agent.description or "",
    }

    try:
        # Create ADK-style agents with memory
        user_agent = SecondMeAgent(
            agent_id=initiator_agent.id,
            user_id=conversation.initiator_user_id,
            profile=initiator_profile,
            partner_profile=receiver_profile
        )

        partner_agent = SecondMeAgent(
            agent_id=receiver_agent.id,
            user_id=conversation.receiver_user_id,
            profile=receiver_profile,
            partner_profile=initiator_profile
        )

        # Generate opening message using A2A protocol
        import uuid
        opening_msg = A2AMessage(
            id=str(uuid.uuid4()),
            sender_agent_id=str(initiator_agent.id),
            receiver_agent_id=str(receiver_agent.id),
            content="",  # Empty for opening
            message_type=MessageType.GREETING,
            conversation_id=str(conversation_id),
            timestamp=datetime.now()
        )

        # Generate opening message
        opening_content = await user_agent.generate_response("")
        opening_msg.content = opening_content

        # Save opening message
        msg = Message(
            conversation_id=conversation_id,
            sender_agent_id=initiator_agent.id,
            content=opening_content
        )
        db.add(msg)
        await db.commit()
        logger.info(f"Conversation {conversation_id}: Opening message sent")

        # Run conversation rounds
        current_message = opening_content

        for round_num in range(settings.agent_conversation_rounds):
            # Partner responds
            partner_response = await partner_agent.generate_response(current_message)

            # Save partner's message
            msg = Message(
                conversation_id=conversation_id,
                sender_agent_id=receiver_agent.id,
                content=partner_response
            )
            db.add(msg)
            await db.commit()
            logger.info(f"Conversation {conversation_id}: Round {round_num + 1}, Partner responded")

            # Small delay
            await asyncio.sleep(0.3)

            # User responds
            user_response = await user_agent.generate_response(partner_response)

            # Save user's message
            msg = Message(
                conversation_id=conversation_id,
                sender_agent_id=initiator_agent.id,
                content=user_response
            )
            db.add(msg)
            await db.commit()
            logger.info(f"Conversation {conversation_id}: Round {round_num + 1}, User responded")

            # Update for next round
            current_message = user_response

            # Small delay between rounds
            await asyncio.sleep(0.3)

        # Calculate heart scores
        user_messages = user_agent.get_conversation_history()
        partner_messages = partner_agent.get_conversation_history()

        user_heart_score = calculate_heart_score(
            agent_profile=initiator_profile,
            partner_profile=receiver_profile,
            messages=user_messages,
            emotional_resonance=0.6
        )

        partner_heart_score = calculate_heart_score(
            agent_profile=receiver_profile,
            partner_profile=initiator_profile,
            messages=partner_messages,
            emotional_resonance=0.6
        )

        # Update conversation with heart scores
        conversation.heart_score_initiator = int(user_heart_score["total_score"])
        conversation.heart_score_receiver = int(partner_heart_score["total_score"])

        # Store heart moments in memory
        if user_heart_score["total_score"] >= 60:
            await user_agent.store_heart_moment(
                moment=f"与{receiver_agent.name}的对话，心动值: {user_heart_score['total_score']}",
                score=user_heart_score["total_score"]
            )

        if partner_heart_score["total_score"] >= 60:
            await partner_agent.store_heart_moment(
                moment=f"与{initiator_agent.name}的对话，心动值: {partner_heart_score['total_score']}",
                score=partner_heart_score["total_score"]
            )

        # Create long-term memories
        await user_agent.create_memory_from_conversation()
        await partner_agent.create_memory_from_conversation()

        # Mark conversation as completed
        conversation.status = "completed"
        conversation.ended_at = datetime.now(timezone.utc)
        await db.commit()

        logger.info(f"Conversation {conversation_id}: Completed. "
                   f"Heart scores - User: {user_heart_score['total_score']}, "
                   f"Partner: {partner_heart_score['total_score']}")

    except Exception as e:
        logger.error(f"Conversation {conversation_id} failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        conversation.status = "failed"
        await db.commit()
