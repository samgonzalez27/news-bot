"""
Authentication routes for login and registration.
"""

from fastapi import APIRouter, status

from src.dependencies import DbSession
from src.exceptions import InvalidCredentialsError
from src.logging_config import get_logger
from src.schemas.auth import LoginRequest, TokenResponse
from src.schemas.user import UserCreate, UserResponse
from src.services.auth_service import AuthService
from src.services.user_service import UserService

logger = get_logger("auth_router")

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="""
    Create a new user account with email, password, and optional preferences.
    
    The password must be at least 8 characters and contain both letters and numbers.
    The preferred_time should be in HH:MM format (24-hour, UTC).
    """,
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Validation error"},
        409: {"description": "Email already registered"},
    },
)
async def register(
    user_data: UserCreate,
    db: DbSession,
) -> UserResponse:
    """Register a new user account."""
    user_service = UserService(db)
    user = await user_service.create_user(user_data)

    logger.info(f"New user registered: {user.email}")

    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and obtain access token",
    description="""
    Authenticate with email and password to receive a JWT access token.
    
    The token should be included in the Authorization header as:
    `Authorization: Bearer <token>`
    
    Token expires after 24 hours by default.
    """,
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
    },
)
async def login(
    credentials: LoginRequest,
    db: DbSession,
) -> TokenResponse:
    """Login with email and password."""
    user_service = UserService(db)
    user = await user_service.verify_credentials(
        email=credentials.email,
        password=credentials.password,
    )

    if not user:
        raise InvalidCredentialsError()

    access_token = AuthService.create_access_token(user.id)
    expires_in = AuthService.get_token_expiry_seconds()

    logger.info(f"User logged in: {user.email}")

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )
