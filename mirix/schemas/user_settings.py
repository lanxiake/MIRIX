from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class UserSettingsBase(BaseModel):
    """Base schema for user settings"""
    chat_model: Optional[str] = Field(None, description="Chat model name")
    memory_model: Optional[str] = Field(None, description="Memory model name")
    timezone: Optional[str] = Field(None, description="User timezone")
    persona: Optional[str] = Field(None, description="Persona name")
    persona_text: Optional[str] = Field(None, description="Custom persona text")
    ui_preferences: Optional[Dict[str, Any]] = Field(None, description="UI preferences")
    custom_settings: Optional[Dict[str, Any]] = Field(None, description="Custom settings")


class UserSettingsCreate(UserSettingsBase):
    """Schema for creating user settings"""
    user_id: str = Field(..., description="User ID")


class UserSettingsUpdate(UserSettingsBase):
    """Schema for updating user settings - all fields are optional"""
    pass


class UserSettingsResponse(UserSettingsBase):
    """Schema for user settings response"""
    user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GetUserSettingsResponse(BaseModel):
    """Response for getting user settings"""
    success: bool
    settings: Optional[UserSettingsResponse]
    message: Optional[str] = None


class UpdateUserSettingsRequest(BaseModel):
    """Request for updating user settings"""
    user_id: str
    settings: UserSettingsUpdate


class UpdateUserSettingsResponse(BaseModel):
    """Response for updating user settings"""
    success: bool
    settings: Optional[UserSettingsResponse]
    message: Optional[str] = None
