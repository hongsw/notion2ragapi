"""Authentication endpoints and utilities."""

from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
import structlog

from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Login request model."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None
    exp: Optional[datetime] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )
        token_data = TokenData(username=username)
        return token_data
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Verify API key from header."""
    if not settings.api_key:
        # If no API key is configured, allow access
        return "no-auth"

    if not x_api_key or x_api_key != settings.api_key:
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return x_api_key


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Get current user from JWT token."""
    token = credentials.credentials
    token_data = verify_token(token)
    return token_data


@router.post("/login", response_model=LoginResponse)
async def login(login_request: LoginRequest) -> LoginResponse:
    """
    Login endpoint for UI authentication.

    This is a simplified implementation. In production, you should:
    1. Store users in a database
    2. Use proper password hashing
    3. Implement user management
    """
    # For demo purposes, using a hardcoded admin user
    # In production, fetch from database
    if login_request.username == "admin" and login_request.password == "admin123":
        access_token = create_access_token(data={"sub": login_request.username})
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_expiration_hours * 3600
        )

    logger.warning("Failed login attempt", username=login_request.username)
    raise HTTPException(
        status_code=401,
        detail="Incorrect username or password"
    )


@router.post("/logout")
async def logout(current_user: TokenData = Depends(get_current_user)) -> Dict[str, str]:
    """
    Logout endpoint.

    Note: With JWT, we can't truly invalidate tokens server-side.
    The client should discard the token.
    """
    logger.info("User logged out", username=current_user.username)
    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_me(current_user: TokenData = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current user information."""
    return {
        "username": current_user.username,
        "is_authenticated": True
    }