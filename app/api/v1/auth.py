from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.schemas.auth import RefreshRequest, TokenResponse, UserLogin, UserRegister, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    return AuthService(db)


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserRegister, svc: Annotated[AuthService, Depends(_auth_service)]):
    """Register a new user account."""
    return await svc.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, svc: Annotated[AuthService, Depends(_auth_service)]):
    """Authenticate and receive JWT tokens."""
    return await svc.login(data.email, data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, svc: Annotated[AuthService, Depends(_auth_service)]):
    """Exchange a refresh token for new token pair."""
    return await svc.refresh(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser):
    """Return current authenticated user."""
    return user
