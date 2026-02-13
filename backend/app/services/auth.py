import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.database import User

logger = logging.getLogger(__name__)


class AuthService:
    """Handles Google OAuth verification, JWT management, and user operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def verify_google_token(self, token: str) -> dict:
        """Verify a Google ID token and return the user info payload."""
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                self.settings.google_client_id,
            )
            if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
                raise ValueError("Invalid issuer")
            return idinfo
        except Exception as e:
            logger.warning(f"Google token verification failed: {e}")
            raise ValueError(f"Invalid Google token: {e}")

    async def get_or_create_user(self, google_info: dict) -> User:
        """Find existing user by google_id or create a new one."""
        google_id = google_info["sub"]
        email = google_info["email"]
        name = google_info.get("name", email)
        picture = google_info.get("picture")

        result = await self.db.execute(
            select(User).where(User.google_id == google_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                id=str(uuid.uuid4()),
                google_id=google_id,
                email=email,
                name=name,
                picture=picture,
            )
            self.db.add(user)
        else:
            user.name = name
            user.picture = picture
            user.email = email
            user.last_login_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    def create_access_token(self, user_id: str) -> str:
        """Create a JWT access token for the given user ID."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "exp": now + timedelta(hours=self.settings.jwt_expiration_hours),
            "iat": now,
        }
        return jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

    def verify_access_token(self, token: str) -> Optional[str]:
        """Verify a JWT access token. Returns user_id if valid, None otherwise."""
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid token: {e}")
            return None
