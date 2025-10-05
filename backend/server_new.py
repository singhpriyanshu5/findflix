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
from auth_utils import *

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# API Keys
TMDB_API_KEY = os.environ['TMDB_API_KEY']
RAPIDAPI_KEY = os.environ['RAPIDAPI_KEY']
OMDB_API_KEY = os.environ['OMDB_API_KEY']
WATCHMODE_API_KEY = os.environ['WATCHMODE_API_KEY']

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

@api_router.post("/swipe/session")
async def create_swipe_session(session_data: CreateSwipeSession, current_user: User = Depends(require_auth)):
    """Create a new swipe session with a friend"""
    try:
        # Verify they are friends
        friendship = await db.friend_requests.find_one({
            "$or": [
                {"sender_id": current_user.id, "receiver_id": session_data.friend_id, "status": "accepted"},
                {"sender_id": session_data.friend_id, "receiver_id": current_user.id, "status": "accepted"}
            ]
        })
        
        if not friendship:
            raise HTTPException(status_code=400, detail="Not friends with this user")
        
        # Create session
        swipe_session = SwipeSession(
            creator_id=current_user.id,
            friend_id=session_data.friend_id,
            content_type=session_data.content_type,
            content_params=session_data.content_params or {}
        )
        
        await db.swipe_sessions.insert_one(swipe_session.dict())
        
        return {"message": "Swipe session created", "session_id": swipe_session.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create swipe session error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create swipe session")

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