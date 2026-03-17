from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, Preference, MatchThreshold
from app.schemas import (
    PreferenceCreate, PreferenceUpdate, PreferenceResponse,
    ThresholdCreate, ThresholdUpdate, ThresholdResponse
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api", tags=["preference"])


@router.post("/preference/set", response_model=PreferenceResponse)
async def set_preference(
    pref_data: PreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if preference exists
    result = await db.execute(select(Preference).where(Preference.user_id == current_user.id))
    preference = result.scalar_one_or_none()

    if preference:
        # Update
        for field, value in pref_data.model_dump().items():
            setattr(preference, field, value)
        await db.commit()
        await db.refresh(preference)
    else:
        # Create
        preference = Preference(**pref_data.model_dump(), user_id=current_user.id)
        db.add(preference)
        await db.commit()
        await db.refresh(preference)

    return PreferenceResponse.model_validate(preference)


@router.get("/preference/my", response_model=PreferenceResponse)
async def get_my_preference(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Preference).where(Preference.user_id == current_user.id))
    preference = result.scalar_one_or_none()

    if not preference:
        raise HTTPException(status_code=404, detail="Preference not found")

    return PreferenceResponse.model_validate(preference)


@router.post("/threshold/set", response_model=ThresholdResponse)
async def set_threshold(
    threshold_data: ThresholdCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if threshold exists
    result = await db.execute(select(MatchThreshold).where(MatchThreshold.user_id == current_user.id))
    threshold = result.scalar_one_or_none()

    if threshold:
        # Update
        threshold.min_heart_score = threshold_data.min_heart_score
        await db.commit()
        await db.refresh(threshold)
    else:
        # Create
        threshold = MatchThreshold(**threshold_data.model_dump(), user_id=current_user.id)
        db.add(threshold)
        await db.commit()
        await db.refresh(threshold)

    return ThresholdResponse.model_validate(threshold)


@router.get("/threshold/my", response_model=ThresholdResponse)
async def get_my_threshold(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MatchThreshold).where(MatchThreshold.user_id == current_user.id))
    threshold = result.scalar_one_or_none()

    if not threshold:
        # Return default
        threshold = MatchThreshold(user_id=current_user.id, min_heart_score=60)

    return ThresholdResponse.model_validate(threshold)
