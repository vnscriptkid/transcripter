import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.database import User
from app.models.schemas import GoogleLoginRequest, LoginResponse, UserResponse
from app.services.auth import AuthService
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/google", response_model=LoginResponse)
async def google_login(
    body: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with a Google ID token."""
    auth_service = AuthService(db)

    try:
        google_info = await auth_service.verify_google_token(body.token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user = await auth_service.get_or_create_user(google_info)
    access_token = auth_service.create_access_token(user.id)

    return LoginResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            picture=user.picture,
        ),
    )


@auth_router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        picture=user.picture,
    )
