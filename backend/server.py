from fastapi import FastAPI, APIRouter, HTTPException, Query, Request, Response, Cookie, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone
import httpx
from enum import Enum

# Import our new models and auth utilities
from models import *
from auth_utils import (
    hash_password,
    verify_password,
    generate_session_token,
    verify_emergent_session,
    create_or_get_user,
    get_user_from_session,
    cleanup_expired_sessions,
    send_password_reset_email
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection with defaults
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'findflix')]

# API Keys with defaults
TMDB_API_KEY = os.environ.get('TMDB_API_KEY', '')
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '')
OMDB_API_KEY = os.environ.get('OMDB_API_KEY', '')
WATCHMODE_API_KEY = os.environ.get('WATCHMODE_API_KEY', '')

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===== Existing Models (keep for backward compatibility) =====
class SearchScope(str, Enum):
    TITLE = "title"
    GENRE = "genre"
    CAST = "cast"
    DIRECTOR = "director"

class SearchHistoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    scope: SearchScope
    genre: Optional[str] = None
    language: Optional[str] = None
    content_type: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SearchRequest(BaseModel):
    query: str
    scope: SearchScope = SearchScope.TITLE
    page: int = 1
    genre: Optional[str] = None
    language: Optional[str] = None
    content_type: Optional[str] = None
    sort_by: Optional[str] = None

# ===== Authentication Dependency =====
async def get_current_user(request: Request, session_token: Optional[str] = Cookie(None)) -> Optional[User]:
    """Get current user from session token (cookie or header)"""
    if not session_token:
        # Fallback to Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if session_token:
        return await get_user_from_session(db, session_token)
    return None

async def require_auth(current_user: User = Depends(get_current_user)) -> User:
    """Require authentication"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user

# ===== Authentication Endpoints =====

@api_router.post("/auth/register")
async def register(user_data: UserRegistration):
    """Register a new user with email/password"""
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        user = User(
            name=user_data.name,
            email=user_data.email
        )
        
        # Hash password and store in separate collection for security
        password_hash = hash_password(user_data.password)
        await db.user_passwords.insert_one({
            "user_id": user.id,
            "password_hash": password_hash
        })
        
        await db.users.insert_one(user.dict())
        
        # Create session
        session_token = generate_session_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            expires_at=expires_at
        )
        await db.user_sessions.insert_one(session.dict())
        
        return {
            "message": "User registered successfully",
            "user": UserProfile(**user.dict()),
            "session_token": session_token
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/auth/login")
async def login(user_data: UserLogin, response: Response):
    """Login with email/password"""
    try:
        # Find user
        user_record = await db.users.find_one({"email": user_data.email})
        if not user_record:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user = User(**user_record)
        
        # Verify password
        password_record = await db.user_passwords.find_one({"user_id": user.id})
        if not password_record or not verify_password(user_data.password, password_record["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create session
        session_token = generate_session_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            expires_at=expires_at
        )
        
        # Remove old sessions
        await db.user_sessions.delete_many({"user_id": user.id})
        await db.user_sessions.insert_one(session.dict())
        
        # Set httpOnly cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=7 * 24 * 60 * 60,  # 7 days
            httponly=True,
            secure=True,
            samesite="none",
            path="/"
        )
        
        return {
            "message": "Login successful",
            "user": UserProfile(**user.dict()),
            "session_token": session_token
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@api_router.post("/auth/forgot-password")
async def forgot_password(request: dict):
    """
    Handle forgot password requests
    - Checks if user exists in database
    - Returns 404 if user doesn't exist
    - Returns 200 if account found (would send email in production)
    """
    try:
        email = request.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Check if user exists in database
        user = await db.users.find_one({"email": email})
        
        if not user:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # TODO: In production, implement actual password reset:
        # 1. Generate secure reset token (uuid4 or secrets.token_urlsafe)
        # 2. Store token in database with expiry (e.g., 1 hour)
        # 3. Send email with reset link containing token
        # 4. Create reset password endpoint that verifies token
        
        logger.info(f"Password reset requested for: {email}")
        
        return {
            "message": "Password reset instructions sent to email",
            "email": email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process request")

@api_router.post("/auth/oauth/session")
async def process_oauth_session(request: Request, response: Response):
    """Process OAuth session from Emergent Auth"""
    try:
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")
        
        # Verify with Emergent Auth
        user_data = await verify_emergent_session(session_id)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        # Create session token
        session_token = user_data["session_token"]
        
        # Create or get user
        user = await create_or_get_user(db, user_data, session_token)
        
        # Set httpOnly cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=7 * 24 * 60 * 60,  # 7 days
            httponly=True,
            secure=True,
            samesite="none",
            path="/"
        )
        
        return {
            "message": "OAuth session processed",
            "user": UserProfile(**user.dict()),
            "session_token": session_token
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth session error: {str(e)}")
        raise HTTPException(status_code=500, detail="OAuth processing failed")

@api_router.get("/auth/me")
async def get_current_user_profile(current_user: User = Depends(require_auth)):
    """Get current user profile"""
    return UserProfile(**current_user.dict())

@api_router.post("/auth/logout")
async def logout(response: Response, current_user: User = Depends(require_auth)):
    """Logout user"""
    try:
        # Delete session from database
        await db.user_sessions.delete_many({"user_id": current_user.id})
        
        # Clear cookie
        response.delete_cookie(
            key="session_token",
            path="/",
            secure=True,
            samesite="none"
        )
        
        return {"message": "Logout successful"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")

# ===== Friend System Endpoints =====

@api_router.post("/friends/request")
async def send_friend_request(request_data: SendFriendRequest, current_user: User = Depends(require_auth)):
    """Send a friend request"""
    try:
        # Find receiver user
        receiver = await db.users.find_one({"email": request_data.receiver_email})
        if not receiver:
            raise HTTPException(status_code=404, detail="User not found")
        
        receiver_user = User(**receiver)
        
        # Don't allow self-requests
        if receiver_user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")
        
        # Check if already friends or request exists
        existing_request = await db.friend_requests.find_one({
            "$or": [
                {"sender_id": current_user.id, "receiver_id": receiver_user.id},
                {"sender_id": receiver_user.id, "receiver_id": current_user.id}
            ]
        })
        
        if existing_request:
            if existing_request["status"] == "accepted":
                raise HTTPException(status_code=400, detail="Already friends")
            else:
                raise HTTPException(status_code=400, detail="Friend request already exists")
        
        # Create friend request
        friend_request = FriendRequest(
            sender_id=current_user.id,
            receiver_id=receiver_user.id
        )
        
        await db.friend_requests.insert_one(friend_request.dict())
        
        return {"message": "Friend request sent successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send friend request error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send friend request")

@api_router.get("/friends/requests")
async def get_friend_requests(current_user: User = Depends(require_auth)):
    """Get pending friend requests"""
    try:
        # Get requests where user is receiver
        requests = await db.friend_requests.find({
            "receiver_id": current_user.id,
            "status": "pending"
        }).to_list(None)
        
        result = []
        for req in requests:
            # Get sender info
            sender_data = await db.users.find_one({"id": req["sender_id"]})
            if sender_data:
                sender = FriendInfo(**sender_data)
                receiver = FriendInfo(**current_user.dict())
                
                result.append(FriendRequestResponse(
                    id=req["id"],
                    sender=sender,
                    receiver=receiver,
                    status=req["status"],
                    created_at=req["created_at"]
                ))
        
        return result
    except Exception as e:
        logger.error(f"Get friend requests error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get friend requests")

@api_router.post("/friends/respond")
async def respond_to_friend_request(response_data: RespondFriendRequest, current_user: User = Depends(require_auth)):
    """Accept or decline a friend request"""
    try:
        # Find the request
        request_record = await db.friend_requests.find_one({
            "id": response_data.request_id,
            "receiver_id": current_user.id,
            "status": "pending"
        })
        
        if not request_record:
            raise HTTPException(status_code=404, detail="Friend request not found")
        
        # Update status
        new_status = "accepted" if response_data.accept else "declined"
        await db.friend_requests.update_one(
            {"id": response_data.request_id},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        message = "Friend request accepted" if response_data.accept else "Friend request declined"
        return {"message": message}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Respond friend request error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to respond to friend request")

@api_router.get("/friends")
async def get_friends(current_user: User = Depends(require_auth)):
    """Get list of friends"""
    try:
        # Find accepted friend requests where user is sender or receiver
        friend_requests = await db.friend_requests.find({
            "$or": [
                {"sender_id": current_user.id, "status": "accepted"},
                {"receiver_id": current_user.id, "status": "accepted"}
            ]
        }).to_list(None)
        
        friends = []
        for req in friend_requests:
            # Get the other user's ID
            friend_id = req["receiver_id"] if req["sender_id"] == current_user.id else req["sender_id"]
            
            # Get friend info
            friend_data = await db.users.find_one({"id": friend_id})
            if friend_data:
                friends.append(FriendInfo(**friend_data))
        
        return friends
    except Exception as e:
        logger.error(f"Get friends error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get friends")

# ===== Swipe System Endpoints =====

@api_router.get("/swipe/session/{friend_id}")
async def get_or_create_session(friend_id: str, current_user: User = Depends(require_auth)):
    """Get existing session or create new one with a friend"""
    try:
        # Verify they are friends
        friendship = await db.friend_requests.find_one({
            "$or": [
                {"sender_id": current_user.id, "receiver_id": friend_id, "status": "accepted"},
                {"sender_id": friend_id, "receiver_id": current_user.id, "status": "accepted"}
            ]
        })
        
        if not friendship:
            raise HTTPException(status_code=400, detail="Not friends with this user")
        
        # Check for existing session between these two users
        existing_session = await db.swipe_sessions.find_one({
            "$or": [
                {"creator_id": current_user.id, "friend_id": friend_id},
                {"creator_id": friend_id, "friend_id": current_user.id}
            ]
        })
        
        if existing_session:
            # Return existing session
            session_id = existing_session["id"]
        else:
            # Create new session with default popular content
            swipe_session = SwipeSession(
                creator_id=current_user.id,
                friend_id=friend_id,
                content_type=SwipeContentType.POPULAR,
                content_params={}
            )
            
            await db.swipe_sessions.insert_one(swipe_session.dict())
            session_id = swipe_session.id
        
        # Get swipe counts
        my_swipes = await db.user_swipes.count_documents({
            "session_id": session_id,
            "user_id": current_user.id
        })
        
        friend_swipes = await db.user_swipes.count_documents({
            "session_id": session_id,
            "user_id": friend_id
        })
        
        # Get match count
        match_count = await db.swipe_matches.count_documents({
            "session_id": session_id
        })
        
        return {
            "session_id": session_id,
            "my_swipes_count": my_swipes,
            "friend_swipes_count": friend_swipes,
            "match_count": match_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get/create session error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get session")

@api_router.get("/swipe/sessions")
async def get_swipe_sessions(current_user: User = Depends(require_auth)):
    """Get active swipe sessions for user"""
    try:
        sessions = await db.swipe_sessions.find({
            "$or": [
                {"creator_id": current_user.id, "is_active": True},
                {"friend_id": current_user.id, "is_active": True}
            ]
        }).sort("created_at", -1).to_list(None)
        
        result = []
        for session in sessions:
            # Get creator and friend info
            creator_data = await db.users.find_one({"id": session["creator_id"]})
            friend_data = await db.users.find_one({"id": session["friend_id"]})
            
            if creator_data and friend_data:
                # Get swipe counts
                my_swipes = await db.user_swipes.count_documents({
                    "session_id": session["id"],
                    "user_id": current_user.id
                })
                
                friend_swipes = await db.user_swipes.count_documents({
                    "session_id": session["id"],
                    "user_id": session["creator_id"] if session["creator_id"] != current_user.id else session["friend_id"]
                })
                
                result.append(SwipeSessionResponse(
                    id=session["id"],
                    creator=FriendInfo(**creator_data),
                    friend=FriendInfo(**friend_data),
                    content_type=session["content_type"],
                    content_params=session["content_params"],
                    is_active=session["is_active"],
                    created_at=session["created_at"],
                    my_swipes_count=my_swipes,
                    friend_swipes_count=friend_swipes
                ))
        
        return result
    except Exception as e:
        logger.error(f"Get swipe sessions error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get swipe sessions")

@api_router.post("/swipe")
async def submit_swipe(swipe_data: SubmitSwipe, current_user: User = Depends(require_auth)):
    """Submit a swipe (like/dislike)"""
    try:
        # Verify user is part of this session
        session = await db.swipe_sessions.find_one({
            "id": swipe_data.session_id,
            "$or": [
                {"creator_id": current_user.id},
                {"friend_id": current_user.id}
            ],
            "is_active": True
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or not authorized")
        
        # Check if already swiped on this movie
        existing_swipe = await db.user_swipes.find_one({
            "session_id": swipe_data.session_id,
            "user_id": current_user.id,
            "movie_id": swipe_data.movie_id,
            "media_type": swipe_data.media_type
        })
        
        if existing_swipe:
            raise HTTPException(status_code=400, detail="Already swiped on this movie")
        
        # Create swipe record
        user_swipe = UserSwipe(
            session_id=swipe_data.session_id,
            user_id=current_user.id,
            movie_id=swipe_data.movie_id,
            media_type=swipe_data.media_type,
            action=swipe_data.action,
            movie_title=swipe_data.movie_title,
            movie_poster=swipe_data.movie_poster
        )
        
        await db.user_swipes.insert_one(user_swipe.dict())
        
        # Check for match if this was a like
        match_created = False
        if swipe_data.action == SwipeAction.LIKE:
            # Find friend's swipe on same movie
            friend_id = session["friend_id"] if session["creator_id"] == current_user.id else session["creator_id"]
            
            friend_swipe = await db.user_swipes.find_one({
                "session_id": swipe_data.session_id,
                "user_id": friend_id,
                "movie_id": swipe_data.movie_id,
                "media_type": swipe_data.media_type,
                "action": "like"
            })
            
            if friend_swipe:
                # Create match
                match = SwipeMatch(
                    session_id=swipe_data.session_id,
                    movie_id=swipe_data.movie_id,
                    media_type=swipe_data.media_type,
                    movie_title=swipe_data.movie_title,
                    movie_poster=swipe_data.movie_poster,
                    user1_id=current_user.id,
                    user2_id=friend_id
                )
                
                await db.swipe_matches.insert_one(match.dict())
                match_created = True
        
        return {
            "message": "Swipe recorded",
            "match_created": match_created
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit swipe error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit swipe")

@api_router.get("/swipe/matches/{session_id}")
async def get_session_matches(session_id: str, current_user: User = Depends(require_auth)):
    """Get matches for a swipe session"""
    try:
        # Verify user is part of this session
        session = await db.swipe_sessions.find_one({
            "id": session_id,
            "$or": [
                {"creator_id": current_user.id},
                {"friend_id": current_user.id}
            ]
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or not authorized")
        
        # Get matches
        matches = await db.swipe_matches.find({
            "session_id": session_id
        }).sort("created_at", -1).to_list(None)
        
        result = []
        for match in matches:
            result.append(SwipeMatchResponse(
                movie_id=match["movie_id"],
                media_type=match["media_type"],
                movie_title=match["movie_title"],
                movie_poster=match["movie_poster"],
                matched_at=match["created_at"]
            ))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session matches error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get matches")

@api_router.get("/swipe/summary/{session_id}")
async def get_session_summary(session_id: str, current_user: User = Depends(require_auth)):
    """Get summary of a swipe session"""
    try:
        # Verify user is part of this session
        session = await db.swipe_sessions.find_one({
            "id": session_id,
            "$or": [
                {"creator_id": current_user.id},
                {"friend_id": current_user.id}
            ]
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or not authorized")
        
        # Get match count and list
        matches = await db.swipe_matches.find({
            "session_id": session_id
        }).sort("created_at", -1).to_list(None)
        
        match_responses = []
        for match in matches:
            match_responses.append(SwipeMatchResponse(
                movie_id=match["movie_id"],
                media_type=match["media_type"],
                movie_title=match["movie_title"],
                movie_poster=match["movie_poster"],
                matched_at=match["created_at"]
            ))
        
        # Get swipe counts
        total_swipes = await db.user_swipes.count_documents({"session_id": session_id})
        creator_swipes = await db.user_swipes.count_documents({
            "session_id": session_id,
            "user_id": session["creator_id"]
        })
        friend_swipes = await db.user_swipes.count_documents({
            "session_id": session_id,
            "user_id": session["friend_id"]
        })
        
        return SessionSummary(
            session_id=session_id,
            total_swipes=total_swipes,
            total_matches=len(matches),
            matches=match_responses,
            creator_swipes=creator_swipes,
            friend_swipes=friend_swipes
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session summary error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get session summary")

@api_router.post("/swipe/session/{session_id}/end")
async def end_swipe_session(session_id: str, current_user: User = Depends(require_auth)):
    """End a swipe session"""
    try:
        # Verify user is creator of this session
        session = await db.swipe_sessions.find_one({
            "id": session_id,
            "creator_id": current_user.id,
            "is_active": True
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or not authorized")
        
        # Mark session as inactive
        await db.swipe_sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        return {"message": "Swipe session ended"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"End swipe session error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to end swipe session")

# ===== Content Endpoints for Swiping =====

@api_router.get("/swipe/content/{session_id}")
async def get_swipe_content(session_id: str, page: int = 1, current_user: User = Depends(require_auth)):
    """Get content for swiping based on session configuration"""
    try:
        # Verify user is part of this session
        session = await db.swipe_sessions.find_one({
            "id": session_id,
            "$or": [
                {"creator_id": current_user.id},
                {"friend_id": current_user.id}
            ],
            "is_active": True
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or not authorized")
        
        # Get content based on session type
        content_type = session["content_type"]
        content_params = session["content_params"]
        
        results = []
        
        if content_type == SwipeContentType.POPULAR:
            # Get popular content
            data = await fetch_tmdb_data("trending/all/week", {"page": page})
            results = data.get("results", [])
            
        elif content_type == SwipeContentType.SEARCH:
            # Use search parameters
            search_request = SearchRequest(
                query=content_params.get("query", ""),
                scope=content_params.get("scope", "title"),
                page=page,
                genre=content_params.get("genre"),
                language=content_params.get("language"),
                content_type=content_params.get("content_type")
            )
            
            # Reuse existing search logic (need to implement this)
            # For now, return popular as fallback
            data = await fetch_tmdb_data("trending/all/week", {"page": page})
            results = data.get("results", [])
            
        elif content_type == SwipeContentType.GENRE:
            # Get content by genre
            genre_id = content_params.get("genre_id")
            if genre_id:
                discover_params = {
                    "with_genres": genre_id,
                    "page": page,
                    "sort_by": "popularity.desc"
                }
                data = await fetch_tmdb_data("discover/movie", discover_params)
                results = data.get("results", [])
        
        # Filter out already swiped content
        swiped_movies = await db.user_swipes.find({
            "session_id": session_id,
            "user_id": current_user.id
        }).to_list(None)
        
        swiped_ids = {(swipe["movie_id"], swipe["media_type"]) for swipe in swiped_movies}
        
        filtered_results = []
        for item in results:
            media_type = item.get("media_type", "movie")
            if media_type not in ["movie", "tv"]:
                continue
            
            movie_id = item.get("id")
            if (movie_id, media_type) not in swiped_ids:
                title = item.get("title") or item.get("name", "")
                year = (item.get("release_date") or item.get("first_air_date", ""))[:4]
                
                filtered_results.append({
                    "id": movie_id,
                    "title": title,
                    "year": year,
                    "media_type": media_type,
                    "poster_path": item.get("poster_path"),
                    "backdrop_path": item.get("backdrop_path"),
                    "overview": item.get("overview", ""),
                    "vote_average": item.get("vote_average", 0),
                    "genres": item.get("genre_ids", [])
                })
        
        return {
            "results": filtered_results,
            "page": page,
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get swipe content error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get swipe content")

# ===== Helper Functions (from original server) =====
async def fetch_tmdb_data(endpoint: str, params: Dict = None):
    """Fetch data from TMDB API"""
    base_url = "https://api.themoviedb.org/3"
    default_params = {"api_key": TMDB_API_KEY}
    if params:
        default_params.update(params)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{base_url}/{endpoint}", params=default_params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"TMDB API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"TMDB API error: {str(e)}")

# Mock data function removed - now using real TMDB API

async def fetch_omdb_data(imdb_id: str):
    """Fetch additional ratings from OMDb API"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                "http://www.omdbapi.com/",
                params={"apikey": OMDB_API_KEY, "i": imdb_id}
            )
            response.raise_for_status()
            data = response.json()
            if data.get("Response") == "False":
                return None
            return data
        except Exception as e:
            logger.error(f"OMDb API error: {str(e)}")
            return None

async def fetch_streaming_availability(tmdb_id: int, media_type: str):
    """Fetch US streaming availability from Streaming Availability API"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"https://streaming-availability.p.rapidapi.com/shows/{media_type}/{tmdb_id}",
                headers={
                    "X-RapidAPI-Key": RAPIDAPI_KEY,
                    "X-RapidAPI-Host": "streaming-availability.p.rapidapi.com"
                },
                params={"series_granularity": "show", "output_language": "en"}
            )
            
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            data = response.json()
            
            streaming_options = data.get("streamingOptions", {}).get("us", [])
            
            grouped = {"stream": [], "rent": [], "buy": []}
            seen_services = {"stream": set(), "rent": set(), "buy": set()}
            
            for option in streaming_options:
                service_name = option.get("service", {}).get("name", "")
                service_id = option.get("service", {}).get("id", "")
                option_type = option.get("type", "").lower()
                link = option.get("link", "")
                
                if option_type in ["subscription", "free"]:
                    category = "stream"
                elif option_type == "rent":
                    category = "rent"
                elif option_type == "buy":
                    category = "buy"
                else:
                    continue
                
                if service_id not in seen_services[category]:
                    grouped[category].append({
                        "name": service_name,
                        "id": service_id,
                        "link": link
                    })
                    seen_services[category].add(service_id)
            
            return grouped
        except Exception as e:
            logger.error(f"Streaming API (RapidAPI) error: {str(e)}")
            return None

def calculate_hit_flop(budget: Optional[int], revenue: Optional[int]) -> str:
    """Calculate hit/flop status"""
    if not budget or not revenue or budget == 0:
        return "Unknown"
    
    ratio = revenue / budget
    if ratio >= 2.0:
        return "Hit"
    elif ratio < 1.0:
        return "Flop"
    else:
        return "Average"

def apply_manual_sort(results: List[Dict], sort_by: Optional[str]) -> List[Dict]:
    """Apply sorting to a list of results (for manual pagination)"""
    if not sort_by:
        # Default: sort by popularity
        results.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    elif sort_by == "rating_desc":
        results.sort(key=lambda x: x.get("vote_average", 0), reverse=True)
    elif sort_by == "rating_asc":
        results.sort(key=lambda x: x.get("vote_average", 0))
    elif sort_by == "year_desc":
        # Sort by release_date or first_air_date, putting items without dates at the end
        results.sort(key=lambda x: (x.get("release_date") or x.get("first_air_date") or "0000-00-00"), reverse=True)
    elif sort_by == "year_asc":
        # Sort by release_date or first_air_date, putting items without dates at the end
        results.sort(key=lambda x: (x.get("release_date") or x.get("first_air_date") or "9999-99-99"))
    
    return results

def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate similarity ratio between two strings (0-1)"""
    str1 = str1.lower().strip()
    str2 = str2.lower().strip()
    
    if str1 == str2:
        return 1.0
    
    # Simple character-based similarity
    if not str1 or not str2:
        return 0.0
    
    # Check if one string contains the other
    if str1 in str2 or str2 in str1:
        return 0.9
    
    # Calculate Levenshtein distance (character differences)
    len1, len2 = len(str1), len(str2)
    if len1 > len2:
        str1, str2 = str2, str1
        len1, len2 = len2, len1
    
    current_row = range(len1 + 1)
    for i in range(1, len2 + 1):
        previous_row, current_row = current_row, [i] + [0] * len1
        for j in range(1, len1 + 1):
            add, delete, change = previous_row[j] + 1, current_row[j-1] + 1, previous_row[j-1]
            if str1[j-1] != str2[i-1]:
                change += 1
            current_row[j] = min(add, delete, change)
    
    distance = current_row[len1]
    max_len = max(len(str1), len(str2))
    similarity = 1 - (distance / max_len)
    
    return similarity

async def fuzzy_search_tmdb(query: str, search_type: str = "multi", page: int = 1) -> Dict:
    """
    Perform fuzzy search with typo tolerance
    Returns TMDB search results even with typos
    """
    # First try exact search
    search_params = {
        "query": query,
        "page": page,
        "include_adult": False
    }
    
    endpoint = f"search/{search_type}"
    try:
        # Try original query first
        data = await fetch_tmdb_data(endpoint, search_params)
        
        # If we got results, return them
        if data.get("results") and len(data["results"]) > 0:
            return data
        
        # If no results, try various fuzzy search strategies
        query_variations = []
        
        # Clean up query (remove special chars, extra spaces)
        cleaned_query = " ".join(query.strip().split())
        if cleaned_query != query:
            query_variations.append(cleaned_query)
        
        # Try common typo corrections for popular terms
        typo_corrections = {
            "spidermn": "spider-man",
            "spiderman": "spider-man",
            "batmn": "batman",
            "supermn": "superman",
            "ironmn": "iron man",
            "captian": "captain",
            "avengrs": "avengers",
            "transformrs": "transformers",
            "jurasic": "jurassic",
            "harrypotter": "harry potter",
            "lordoftherings": "lord of the rings",
            "starwrs": "star wars",
            "startrek": "star trek"
        }
        
        query_lower = query.lower().replace(" ", "").replace("-", "")
        for typo, correction in typo_corrections.items():
            if typo in query_lower:
                corrected = query.lower().replace(typo, correction)
                query_variations.append(corrected)
        
        # Try removing common words that might cause issues
        common_words = ["the", "a", "an", "of", "and", "or", "but", "in", "on", "at", "to", "for", "with"]
        words = query.lower().split()
        if len(words) > 1:
            filtered_words = [w for w in words if w not in common_words]
            if len(filtered_words) > 0 and len(filtered_words) < len(words):
                query_variations.append(" ".join(filtered_words))
        
        # Try each variation
        for variation in query_variations:
            if variation and variation != query:
                search_params["query"] = variation
                data = await fetch_tmdb_data(endpoint, search_params)
                if data.get("results") and len(data["results"]) > 0:
                    return data
        
        # Return empty results if nothing found
        return {"results": [], "total_pages": 0}
        
    except Exception as e:
        logger.error(f"Fuzzy search error: {str(e)}")
        return {"results": [], "total_pages": 0}

# ===== Original Movie/TV Endpoints =====

@api_router.post("/search")
async def search_titles(request: SearchRequest):
    """Search for movies/TV shows with filters"""
    try:
        # Save to search history (only if user is authenticated)
        # For now, skip history to maintain backward compatibility
        
        results = []
        
        if request.scope == SearchScope.TITLE:
            # Use fuzzy search for better typo tolerance
            data = await fuzzy_search_tmdb(request.query, "multi", request.page)
            results = data.get("results", [])
            total_pages = data.get("total_pages", 1)
            
        elif request.scope == SearchScope.GENRE:
            genres_movie = await fetch_tmdb_data("genre/movie/list")
            genres_tv = await fetch_tmdb_data("genre/tv/list")
            all_genres = genres_movie.get("genres", []) + genres_tv.get("genres", [])
            
            matching_genre = next((g for g in all_genres if request.query.lower() in g["name"].lower()), None)
            
            if matching_genre:
                discover_params = {
                    "with_genres": matching_genre["id"],
                    "page": request.page,
                    "sort_by": "popularity.desc"
                }
                if request.language:
                    discover_params["with_original_language"] = request.language
                
                data = await fetch_tmdb_data("discover/movie", discover_params)
                results = data.get("results", [])
                total_pages = data.get("total_pages", 1)
            else:
                results = []
                total_pages = 1
                
        elif request.scope == SearchScope.CAST:
            person_data = await fetch_tmdb_data("search/person", {
                "query": request.query,
                "page": 1
            })
            persons = person_data.get("results", [])
            
            if persons:
                persons.sort(key=lambda x: x.get("popularity", 0), reverse=True)
                person_id = persons[0]["id"]
                
                if request.genre:
                    discover_params = {
                        "with_cast": person_id,
                        "page": request.page,
                        "sort_by": "popularity.desc"
                    }
                    if request.genre:
                        discover_params["with_genres"] = request.genre
                    
                    data = await fetch_tmdb_data("discover/movie", discover_params)
                    results = data.get("results", [])
                    total_pages = data.get("total_pages", 1)
                else:
                    credits = await fetch_tmdb_data(f"person/{person_id}/combined_credits")
                    cast_results = credits.get("cast", [])
                    
                    cast_results.sort(key=lambda x: x.get("popularity", 0), reverse=True)
                    start_idx = (request.page - 1) * 20
                    end_idx = start_idx + 20
                    results = cast_results[start_idx:end_idx]
                    total_pages = (len(cast_results) + 19) // 20
            else:
                results = []
                total_pages = 1
                
        elif request.scope == SearchScope.DIRECTOR:
            person_data = await fetch_tmdb_data("search/person", {
                "query": request.query,
                "page": 1
            })
            persons = person_data.get("results", [])
            
            if persons:
                persons.sort(key=lambda x: x.get("popularity", 0), reverse=True)
                person_id = persons[0]["id"]
                
                if request.genre:
                    discover_params = {
                        "with_crew": person_id,
                        "page": request.page,
                        "sort_by": "popularity.desc"
                    }
                    if request.genre:
                        discover_params["with_genres"] = request.genre
                    
                    data = await fetch_tmdb_data("discover/movie", discover_params)
                    results = data.get("results", [])
                    total_pages = data.get("total_pages", 1)
                else:
                    credits = await fetch_tmdb_data(f"person/{person_id}/combined_credits")
                    crew_results = [c for c in credits.get("crew", []) if c.get("job") == "Director"]
                    
                    crew_results.sort(key=lambda x: x.get("popularity", 0), reverse=True)
                    start_idx = (request.page - 1) * 20
                    end_idx = start_idx + 20
                    results = crew_results[start_idx:end_idx]
                    total_pages = (len(crew_results) + 19) // 20
            else:
                results = []
                total_pages = 1
        
        # Format results
        formatted_results = []
        for item in results:
            media_type = item.get("media_type", "movie")
            if media_type not in ["movie", "tv"]:
                continue
            
            if request.content_type:
                if request.content_type == "movie" and media_type != "movie":
                    continue
                elif request.content_type == "tv" and media_type != "tv":
                    continue
            
            if request.genre:
                item_genres = item.get("genre_ids", [])
                if int(request.genre) not in item_genres:
                    continue
            
            if request.language:
                item_language = item.get("original_language", "")
                if item_language != request.language:
                    continue
            
            title = item.get("title") or item.get("name", "")
            year = (item.get("release_date") or item.get("first_air_date", ""))[:4]
            tmdb_id = item.get("id")
            
            imdb_rating = item.get("vote_average", 0)
            try:
                external_ids_data = await fetch_tmdb_data(f"{media_type}/{tmdb_id}/external_ids")
                imdb_id = external_ids_data.get("imdb_id")
                
                if imdb_id:
                    omdb_data = await fetch_omdb_data(imdb_id)
                    if omdb_data:
                        omdb_rating = omdb_data.get("imdbRating")
                        if omdb_rating and omdb_rating != "N/A":
                            imdb_rating = float(omdb_rating)
            except Exception as e:
                logger.error(f"Error fetching IMDb rating for {tmdb_id}: {str(e)}")
            
            formatted_item = {
                "id": tmdb_id,
                "title": title,
                "year": year,
                "media_type": media_type,
                "poster_path": item.get("poster_path"),
                "genres": item.get("genre_ids", []),
                "vote_average": imdb_rating,
                "overview": item.get("overview", ""),
                "original_language": item.get("original_language", "")
            }
            formatted_results.append(formatted_item)
        
        # Apply sorting if specified
        if request.sort_by:
            if request.sort_by == "rating_desc":
                formatted_results.sort(key=lambda x: x["vote_average"], reverse=True)
            elif request.sort_by == "rating_asc":
                formatted_results.sort(key=lambda x: x["vote_average"])
            elif request.sort_by == "year_desc":
                formatted_results.sort(key=lambda x: x["year"] or "0", reverse=True)
            elif request.sort_by == "year_asc":
                formatted_results.sort(key=lambda x: x["year"] or "0")
        
        return {
            "results": formatted_results,
            "page": request.page,
            "total_pages": total_pages
        }
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/title/{tmdb_id}")
async def get_title_details(tmdb_id: int, media_type: str = Query("movie", regex="^(movie|tv)$")):
    """Get detailed information for a specific title"""
    try:
        endpoint = f"{media_type}/{tmdb_id}"
        tmdb_data = await fetch_tmdb_data(endpoint, {"append_to_response": "credits,external_ids"})
        
        imdb_id = tmdb_data.get("external_ids", {}).get("imdb_id")
        
        omdb_data = None
        if imdb_id:
            omdb_data = await fetch_omdb_data(imdb_id)
        
        ratings = {
            "tmdb": tmdb_data.get("vote_average", 0),
            "imdb": tmdb_data.get("vote_average", 0),
            "imdb_votes": None,
            "rotten_tomatoes_critics": None,
            "rotten_tomatoes_audience": None,
            "metacritic": None,
            "google_users": None
        }
        
        if omdb_data:
            omdb_ratings = omdb_data.get("Ratings", [])
            for rating in omdb_ratings:
                source = rating.get("Source", "")
                value = rating.get("Value", "")
                
                if "Rotten Tomatoes" in source:
                    if "%" in value:
                        ratings["rotten_tomatoes_critics"] = int(value.replace("%", ""))
                elif "Metacritic" in source:
                    if "/" in value:
                        ratings["metacritic"] = int(value.split("/")[0])
            
            imdb_rating = omdb_data.get("imdbRating")
            if imdb_rating and imdb_rating != "N/A":
                ratings["imdb"] = float(imdb_rating)
            
            imdb_votes = omdb_data.get("imdbVotes")
            if imdb_votes and imdb_votes != "N/A":
                ratings["imdb_votes"] = imdb_votes
        
        title = tmdb_data.get("title") or tmdb_data.get("name", "")
        year = (tmdb_data.get("release_date") or tmdb_data.get("first_air_date", ""))[:4]
        
        result = {
            "id": tmdb_id,
            "title": title,
            "year": year,
            "media_type": media_type,
            "poster_path": tmdb_data.get("poster_path"),
            "backdrop_path": tmdb_data.get("backdrop_path"),
            "overview": tmdb_data.get("overview", ""),
            "genres": [g["name"] for g in tmdb_data.get("genres", [])],
            "ratings": ratings,
            "tagline": tmdb_data.get("tagline", ""),
            "original_language": tmdb_data.get("original_language", ""),
            "imdb_id": imdb_id
        }
        
        if media_type == "movie":
            budget = tmdb_data.get("budget", 0)
            revenue = tmdb_data.get("revenue", 0)
            result["runtime"] = tmdb_data.get("runtime")
            result["budget"] = budget
            result["box_office"] = revenue
            result["hit_flop_status"] = calculate_hit_flop(budget, revenue)
        else:
            result["seasons"] = tmdb_data.get("number_of_seasons", 0)
            result["episodes"] = tmdb_data.get("number_of_episodes", 0)
            episode_runtimes = tmdb_data.get("episode_run_time", [])
            
            if not episode_runtimes:
                try:
                    season_data = await fetch_tmdb_data(f"tv/{tmdb_id}/season/1")
                    episodes = season_data.get("episodes", [])
                    if episodes:
                        runtimes = [ep.get("runtime") for ep in episodes if ep.get("runtime")]
                        if runtimes:
                            result["episode_runtime"] = int(sum(runtimes) / len(runtimes))
                        else:
                            result["episode_runtime"] = None
                    else:
                        result["episode_runtime"] = None
                except Exception as e:
                    logger.error(f"Error fetching season data: {str(e)}")
                    result["episode_runtime"] = None
            else:
                result["episode_runtime"] = episode_runtimes[0]
        
        credits = tmdb_data.get("credits", {})
        cast = credits.get("cast", [])[:5]
        result["cast"] = [{"name": c.get("name"), "character": c.get("character")} for c in cast]
        
        crew = credits.get("crew", [])
        directors = [c["name"] for c in crew if c.get("job") == "Director"][:3]
        producers = [c["name"] for c in crew if c.get("job") == "Producer"][:3]
        
        result["directors"] = directors
        result["producers"] = producers
        result["production_companies"] = [pc.get("name") for pc in tmdb_data.get("production_companies", [])[:3]]
        
        return result
        
    except Exception as e:
        logger.error(f"Title details error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/streaming/{tmdb_id}")
async def get_streaming_availability_endpoint(tmdb_id: int, media_type: str = Query("movie", regex="^(movie|tv)$")):
    """Get US streaming availability for a title"""
    try:
        streaming_data = await fetch_streaming_availability(tmdb_id, media_type)
        
        if not streaming_data:
            return {
                "available": False,
                "stream": [],
                "rent": [],
                "buy": []
            }
        
        return {
            "available": True,
            **streaming_data
        }
        
    except Exception as e:
        logger.error(f"Streaming availability error: {str(e)}")
        return {
            "available": False,
            "stream": [],
            "rent": [],
            "buy": [],
            "error": "Streaming availability temporarily unavailable"
        }

@api_router.get("/popular")
async def get_popular_titles(page: int = 1):
    """Get popular/trending titles"""
    try:
        trending = await fetch_tmdb_data("trending/all/week", {"page": page})
        
        results = []
        for item in trending.get("results", []):
            media_type = item.get("media_type", "movie")
            if media_type not in ["movie", "tv"]:
                continue
            
            title = item.get("title") or item.get("name", "")
            year = (item.get("release_date") or item.get("first_air_date", ""))[:4]
            
            results.append({
                "id": item.get("id"),
                "title": title,
                "year": year,
                "media_type": media_type,
                "poster_path": item.get("poster_path"),
                "genres": item.get("genre_ids", []),
                "vote_average": item.get("vote_average", 0)
            })
        
        return {
            "results": results,
            "page": page,
            "total_pages": trending.get("total_pages", 1)
        }
        
    except Exception as e:
        logger.error(f"Popular titles error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/search/history")
async def get_search_history_endpoint(limit: int = 10, current_user: User = Depends(get_current_user)):
    """Get recent search history (requires authentication)"""
    if not current_user:
        return []
    
    try:
        history = await db.search_history.find(
            {"user_id": current_user.id}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        return [SearchHistoryItem(**item) for item in history]
    except Exception as e:
        logger.error(f"Search history error: {str(e)}")
        return []

@api_router.delete("/search/history")
async def clear_search_history_endpoint(current_user: User = Depends(require_auth)):
    """Clear search history"""
    try:
        await db.search_history.delete_many({"user_id": current_user.id})
        return {"message": "Search history cleared"}
    except Exception as e:
        logger.error(f"Clear history error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/genres")
async def get_genres():
    """Get all available genres"""
    try:
        movie_genres = await fetch_tmdb_data("genre/movie/list")
        tv_genres = await fetch_tmdb_data("genre/tv/list")
        
        all_genres = {}
        for g in movie_genres.get("genres", []) + tv_genres.get("genres", []):
            all_genres[g["id"]] = g["name"]
        
        return {"genres": all_genres}
    except Exception as e:
        logger.error(f"Genres error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/search/fuzzy")
async def fuzzy_search_endpoint(query: str, media_type: str = "multi", page: int = 1):
    """
    Fuzzy search endpoint with typo tolerance
    Supports: multi, movie, tv, person
    """
    try:
        if not query or len(query.strip()) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
        
        # Validate media_type
        valid_types = ["multi", "movie", "tv", "person"]
        if media_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid media_type. Must be one of: {valid_types}")
        
        # Use fuzzy search
        data = await fuzzy_search_tmdb(query.strip(), media_type, page)
        results = data.get("results", [])
        total_pages = data.get("total_pages", 1)
        
        # Format results similar to regular search
        formatted_results = []
        for item in results:
            item_media_type = item.get("media_type", media_type if media_type != "multi" else "movie")
            
            if item_media_type not in ["movie", "tv", "person"]:
                continue
            
            if item_media_type == "person":
                formatted_item = {
                    "id": item.get("id"),
                    "name": item.get("name", ""),
                    "media_type": "person",
                    "profile_path": item.get("profile_path"),
                    "known_for_department": item.get("known_for_department", ""),
                    "popularity": item.get("popularity", 0)
                }
            else:
                title = item.get("title") or item.get("name", "")
                year = (item.get("release_date") or item.get("first_air_date", ""))[:4]
                
                formatted_item = {
                    "id": item.get("id"),
                    "title": title,
                    "year": year,
                    "media_type": item_media_type,
                    "poster_path": item.get("poster_path"),
                    "genres": item.get("genre_ids", []),
                    "vote_average": item.get("vote_average", 0),
                    "overview": item.get("overview", ""),
                    "original_language": item.get("original_language", ""),
                    "popularity": item.get("popularity", 0)
                }
            
            formatted_results.append(formatted_item)
        
        return {
            "results": formatted_results,
            "page": page,
            "total_pages": total_pages,
            "query": query,
            "media_type": media_type,
            "fuzzy_search": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fuzzy search endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@api_router.get("/")
async def root():
    return {"message": "FindFlix API with Tinder Feature", "status": "running"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Cleanup task
@app.on_event("startup")
async def startup_event():
    # Clean up expired sessions on startup
    await cleanup_expired_sessions(db)