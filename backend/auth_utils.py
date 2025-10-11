import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
import httpx
import os
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import User, UserSession
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """Hash a password with salt"""
    salt = secrets.token_hex(32)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${password_hash.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        salt, password_hash = hashed.split('$')
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return password_hash == new_hash.hex()
    except:
        return False

def generate_session_token() -> str:
    """Generate a secure session token"""
    return secrets.token_urlsafe(64)

async def verify_emergent_session(session_id: str) -> Optional[dict]:
    """Verify session with Emergent Auth service"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        logger.error(f"Error verifying Emergent session: {str(e)}")
        return None

async def create_or_get_user(db: AsyncIOMotorDatabase, user_data: dict, session_token: str) -> User:
    """Create or get user from OAuth data"""
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data["email"]})
    
    if existing_user:
        user = User(**existing_user)
    else:
        # Create new user
        user = User(
            name=user_data["name"],
            email=user_data["email"],
            picture=user_data.get("picture")
        )
        await db.users.insert_one(user.dict())
    
    # Create or update session
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session = UserSession(
        user_id=user.id,
        session_token=session_token,
        expires_at=expires_at
    )
    
    # Remove old sessions for this user
    await db.user_sessions.delete_many({"user_id": user.id})
    await db.user_sessions.insert_one(session.dict())
    
    return user

async def get_user_from_session(db: AsyncIOMotorDatabase, session_token: str) -> Optional[User]:
    """Get user from session token"""
    try:
        # Find active session
        session_data = await db.user_sessions.find_one({
            "session_token": session_token,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        if not session_data:
            return None
        
        # Get user
        user_data = await db.users.find_one({"id": session_data["user_id"]})
        if user_data:
            return User(**user_data)
        
        return None
    except Exception as e:
        logger.error(f"Error getting user from session: {str(e)}")
        return None

async def cleanup_expired_sessions(db: AsyncIOMotorDatabase):
    """Clean up expired sessions"""
    try:
        result = await db.user_sessions.delete_many({
            "expires_at": {"$lt": datetime.now(timezone.utc)}
        })
        logger.info(f"Cleaned up {result.deleted_count} expired sessions")
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {str(e)}")