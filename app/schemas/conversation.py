from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ConversationBase(BaseModel):
    pass


class ConversationResponse(BaseModel):
    id: int
    initiator_agent_id: int
    receiver_agent_id: int
    initiator_user_id: int
    receiver_user_id: int
    status: str
    heart_score_initiator: Optional[int] = None
    heart_score_receiver: Optional[int] = None
    started_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_agent_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []


class PoolStatusResponse(BaseModel):
    in_pool: bool
    status: Optional[str] = None
    matched_conversation_id: Optional[int] = None
    waiting_time: Optional[int] = None  # seconds


class JoinPoolResponse(BaseModel):
    success: bool
    message: str
    pool_entry_id: Optional[int] = None


class EscalateResponse(BaseModel):
    success: bool
    message: str


class HeartScoreResponse(BaseModel):
    conversation_id: int
    initiator_heart_score: int
    receiver_heart_score: int
    both_match_threshold: bool
    can_escalate: bool
    details: dict
