from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None


class WeChatCallback(BaseModel):
    code: str


class UserResponse(BaseModel):
    id: int
    username: Optional[str] = None
    email: Optional[str] = None
    is_premium: bool
    is_active: bool
    wechat_nickname: Optional[str] = None
    wechat_avatar: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class WeChatQRCodeResponse(BaseModel):
    qrcode_url: str
    state: str  # Used to track the login session
