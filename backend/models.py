from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

# User and Authentication Models

class UserRegistration(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class UserSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Friend System Models

class FriendRequestStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"

class FriendRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    receiver_id: str
    status: FriendRequestStatus = FriendRequestStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SendFriendRequest(BaseModel):
    receiver_email: EmailStr

class RespondFriendRequest(BaseModel):
    request_id: str
    accept: bool

# Swipe System Models

class SwipeAction(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"

class SwipeContentType(str, Enum):
    POPULAR = "popular"
    SEARCH = "search"
    GENRE = "genre"

class SwipeSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    creator_id: str
    friend_id: str
    content_type: SwipeContentType
    content_params: Dict[str, Any] = {}  # Store search query, genre id, etc.
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CreateSwipeSession(BaseModel):
    friend_id: str
    content_type: SwipeContentType
    content_params: Optional[Dict[str, Any]] = {}

class UserSwipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str
    movie_id: int
    media_type: str  # "movie" or "tv"
    action: SwipeAction
    movie_title: str
    movie_poster: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SubmitSwipe(BaseModel):
    session_id: str
    movie_id: int
    media_type: str
    action: SwipeAction
    movie_title: str
    movie_poster: Optional[str] = None

class SwipeMatch(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    movie_id: int
    media_type: str
    movie_title: str
    movie_poster: Optional[str] = None
    user1_id: str
    user2_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Response Models

class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    picture: Optional[str]
    created_at: datetime

class FriendInfo(BaseModel):
    id: str
    name: str
    email: str
    picture: Optional[str]

class FriendRequestResponse(BaseModel):
    id: str
    sender: FriendInfo
    receiver: FriendInfo
    status: FriendRequestStatus
    created_at: datetime

class SwipeSessionResponse(BaseModel):
    id: str
    creator: FriendInfo
    friend: FriendInfo
    content_type: SwipeContentType
    content_params: Dict[str, Any]
    is_active: bool
    created_at: datetime
    my_swipes_count: int
    friend_swipes_count: int

class SwipeMatchResponse(BaseModel):
    movie_id: int
    media_type: str
    movie_title: str
    movie_poster: Optional[str]
    matched_at: datetime

class SessionSummary(BaseModel):
    session_id: str
    total_swipes: int
    total_matches: int
    matches: List[SwipeMatchResponse]
    creator_swipes: int
    friend_swipes: int