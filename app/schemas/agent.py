from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AgentBase(BaseModel):
    name: str
    gender: str  # male/female/other
    age: int
    height: Optional[int] = None
    weight: Optional[int] = None
    personality: Optional[Dict[str, Any]] = None
    hobbies: Optional[List[str]] = None
    industry: Optional[str] = None
    job_title: Optional[str] = None
    speaking_style: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    personality: Optional[Dict[str, Any]] = None
    hobbies: Optional[List[str]] = None
    industry: Optional[str] = None
    job_title: Optional[str] = None
    speaking_style: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None


class AgentResponse(AgentBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentDiscoverResponse(BaseModel):
    agents: List[AgentResponse]
    total: int
