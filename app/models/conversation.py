from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)

    # Agents involved
    initiator_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    receiver_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Real users involved
    initiator_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Status
    status = Column(String, default="running")  # pending/running/completed/matched/escalated

    # Heart scores
    heart_score_initiator = Column(Integer, nullable=True)
    heart_score_receiver = Column(Integer, nullable=True)

    # Timestamps
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
