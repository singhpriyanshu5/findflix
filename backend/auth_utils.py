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

def send_password_reset_email(email: str, reset_token: str, app_url: str = "https://findflix-2.emergent.host"):
    """
    Send password reset email using SMTP
    Supports Gmail, SendGrid, or any SMTP server
    """
    try:
        # Get email configuration from environment variables
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        from_email = os.getenv("FROM_EMAIL", smtp_username)
        
        if not smtp_username or not smtp_password:
            logger.warning("SMTP credentials not configured. Email not sent.")
            return False
        
        # Create reset link
        reset_link = f"{app_url}/reset-password?token={reset_token}"
        
        # Create email message
        message = MIMEMultipart("alternative")
        message["Subject"] = "FindFlix - Password Reset Request"
        message["From"] = from_email
        message["To"] = email
        
        # Email body (HTML)
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
              <h2 style="color: #e50914;">FindFlix Password Reset</h2>
              <p>Hi there,</p>
              <p>We received a request to reset your password. Click the button below to create a new password:</p>
              <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" 
                   style="background-color: #e50914; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                  Reset Password
                </a>
              </div>
              <p>Or copy and paste this link into your browser:</p>
              <p style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; word-break: break-all;">
                {reset_link}
              </p>
              <p><strong>This link will expire in 1 hour.</strong></p>
              <p>If you didn't request this password reset, please ignore this email.</p>
              <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
              <p style="color: #999; font-size: 12px;">
                FindFlix - Find your next movie to watch<br>
                This is an automated message, please do not reply.
              </p>
            </div>
          </body>
        </html>
        """
        
        # Plain text version
        text = f"""
        FindFlix Password Reset
        
        Hi there,
        
        We received a request to reset your password. Click the link below to create a new password:
        
        {reset_link}
        
        This link will expire in 1 hour.
        
        If you didn't request this password reset, please ignore this email.
        
        ---
        FindFlix - Find your next movie to watch
        """
        
        # Attach both versions
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(from_email, email, message.as_string())
        
        logger.info(f"Password reset email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        return False