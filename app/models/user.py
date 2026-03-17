from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    is_premium = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # WeChat fields
    wechat_openid = Column(String, unique=True, index=True, nullable=True)
    wechat_unionid = Column(String, index=True, nullable=True)
    wechat_nickname = Column(String, nullable=True)
    wechat_avatar = Column(String, nullable=True)
