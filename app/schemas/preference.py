from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PreferenceBase(BaseModel):
    target_gender: Optional[str] = None  # male/female/any
    age_range_min: int = 18
    age_range_max: int = 50
    height_range_min: Optional[int] = None
    height_range_max: Optional[int] = None
    industries: Optional[List[str]] = None
    hobbies: Optional[List[str]] = None


class PreferenceCreate(PreferenceBase):
    pass


class PreferenceUpdate(BaseModel):
    target_gender: Optional[str] = None
    age_range_min: Optional[int] = None
    age_range_max: Optional[int] = None
    height_range_min: Optional[int] = None
    height_range_max: Optional[int] = None
    industries: Optional[List[str]] = None
    hobbies: Optional[List[str]] = None


class PreferenceResponse(PreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ThresholdBase(BaseModel):
    min_heart_score: int = 60


class ThresholdCreate(ThresholdBase):
    pass


class ThresholdUpdate(BaseModel):
    min_heart_score: int


class ThresholdResponse(ThresholdBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
