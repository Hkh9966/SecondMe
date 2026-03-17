from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import httpx
import uuid

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, Token, WeChatQRCodeResponse, WeChatCallback
from app.services.auth_utils import verify_password, get_password_hash, create_access_token, decode_access_token
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# In-memory storage for WeChat login sessions (in production, use Redis)
wechat_sessions = {}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create token
    access_token = create_access_token(data={"sub": user.id})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(data={"sub": user.id})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/wechat/qrcode", response_model=WeChatQRCodeResponse)
async def get_wechat_qrcode():
    """Get WeChat login QR code URL"""
    state = str(uuid.uuid4())

    # Store session
    wechat_sessions[state] = {"status": "pending", "created_at": datetime.utcnow()}

    # Generate WeChat QR code URL (this is a placeholder - actual implementation depends on WeChat API)
    # For actual WeChat login, you would use the WeChat Open Platform API
    qrcode_url = f"https://open.weixin.qq.com/connect/qrconnect?appid={settings.wechat_app_id}&redirect_uri={settings.wechat_redirect_uri}&response_type=code&scope=snsapi_login&state={state}#wechat_redirect"

    return WeChatQRCodeResponse(qrcode_url=qrcode_url, state=state)


@router.get("/wechat/callback")
async def wechat_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """Handle WeChat OAuth callback"""
    if state not in wechat_sessions:
        raise HTTPException(status_code=400, detail="Invalid state")

    session = wechat_sessions[state]

    try:
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            token_url = f"https://api.weixin.qq.com/sns/oauth2/access_token?appid={settings.wechat_app_id}&secret={settings.wechat_app_secret}&code={code}&grant_type=authorization_code"
            response = await client.get(token_url)
            token_data = response.json()

            if "errcode" in token_data:
                raise HTTPException(status_code=400, detail=f"WeChat API error: {token_data.get('errmsg')}")

            access_token = token_data["access_token"]
            openid = token_data["openid"]
            unionid = token_data.get("unionid", "")

            # Get user info
            userinfo_url = f"https://api.weixin.qq.com/sns/userinfo?access_token={access_token}&openid={openid}&lang=zh_CN"
            userinfo_response = await client.get(userinfo_url)
            userinfo = userinfo_response.json()

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to authenticate with WeChat: {str(e)}")

    # Check if user exists
    result = await db.execute(select(User).where(User.wechat_openid == openid))
    user = result.scalar_one_or_none()

    if user:
        # Update user info
        user.wechat_nickname = userinfo.get("nickname")
        user.wechat_avatar = userinfo.get("headimgurl")
        await db.commit()
    else:
        # Create new user
        user = User(
            username=f"wechat_{openid[:8]}",
            wechat_openid=openid,
            wechat_unionid=unionid,
            wechat_nickname=userinfo.get("nickname"),
            wechat_avatar=userinfo.get("headimgurl"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Create token
    access_token = create_access_token(data={"sub": user.id})

    # Clean up session
    del wechat_sessions[state]

    # Redirect to frontend with token (in production, this would be handled by the frontend)
    return {"access_token": access_token, "token_type": "bearer", "user": UserResponse.model_validate(user)}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # In a more complete implementation, you would invalidate the token
    return {"message": "Successfully logged out"}
