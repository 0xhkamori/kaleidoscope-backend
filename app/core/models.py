from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: str
    password: str
    handle: str

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class User(BaseModel):
    userId: str
    email: str
    passwordHash: str
    createdAt: datetime

class Session(BaseModel):
    sessionId: str
    userId: str
    refreshToken: str
    userAgent: Optional[str]
    expiresAt: datetime

class ProfileUpdate(BaseModel):
    handle: Optional[str] = None
    displayName: Optional[str] = None
    bio: Optional[str] = None
    avatarUrl: Optional[str] = None

class TagCreate(BaseModel):
    text: str
    iconName: Optional[str] = None
    color: Optional[str] = None

class Tag(BaseModel):
    id: str
    profileId: str
    text: str
    iconName: Optional[str] = None
    color: Optional[str] = None

class Profile(BaseModel):
    id: str
    userId: str
    handle: Optional[str] = None
    displayName: Optional[str] = None
    bio: Optional[str] = None
    avatarUrl: Optional[str] = None
    avatarDeleteUrl: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    tags: List[Tag] = []

class ProfilePublic(BaseModel):
    handle: str
    displayName: str
    bio: Optional[str] = None
    avatarUrl: Optional[str] = None
    tags: List[Tag] = []

class AvatarUpload(BaseModel):
    imageBase64: str  # Base64 encoded image data (e.g., "data:image/png;base64,iVBORw0KGgo...")