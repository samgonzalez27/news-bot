"""
FastAPI dependencies for the News Digest API.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.exceptions import AuthenticationError
from src.models.user import User
from src.services.auth_service import AuthService
from src.services.user_service import UserService


class HTTPBearerWith401(HTTPBearer):
    """
    Custom HTTPBearer that returns 401 Unauthorized instead of 403 Forbidden.
    
    Per HTTP spec, 401 is correct for missing authentication, while 403 is for
    insufficient permissions. FastAPI's default HTTPBearer returns 403.
    """
    
    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        authorization = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)
        
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)


# HTTP Bearer security scheme for OpenAPI/Swagger UI integration
# This automatically adds securitySchemes to OpenAPI spec and shows "Authorize" button
bearer_scheme = HTTPBearerWith401(
    scheme_name="bearerAuth",
    description="JWT access token. Obtain via POST /api/v1/auth/login",
    auto_error=True,  # Automatically return 401 if no token provided
)


async def get_token_from_header(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> str:
    """
    Extract JWT token from Authorization header.

    Uses HTTPBearer security scheme for proper OpenAPI integration.
    The HTTPBearer dependency handles:
    - Validating the "Bearer" prefix
    - Extracting the token
    - Generating OpenAPI securitySchemes
    - Showing "Authorize" button in Swagger UI

    Args:
        credentials: HTTP Authorization credentials from HTTPBearer.

    Returns:
        str: JWT token.

    Raises:
        HTTPException: 401 if header is missing or invalid (handled by HTTPBearer).
    """
    return credentials.credentials


async def get_current_user_id(
    token: Annotated[str, Depends(get_token_from_header)],
) -> UUID:
    """
    Get the current user's ID from the JWT token.

    Args:
        token: JWT token from header.

    Returns:
        UUID: User's unique identifier.

    Raises:
        AuthenticationError: If token is invalid.
    """
    return AuthService.get_user_id_from_token(token)


async def get_current_user(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get the current authenticated user.

    Args:
        user_id: User ID from token.
        db: Database session.

    Returns:
        User: Current user object.

    Raises:
        AuthenticationError: If user not found or inactive.
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise AuthenticationError("User not found")

    if not user.is_active:
        raise AuthenticationError("User account is deactivated")

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Alias for get_current_user that explicitly requires active status.

    This is semantically clearer in route definitions.

    Args:
        current_user: Current authenticated user.

    Returns:
        User: Active user object.
    """
    return current_user


# Type aliases for cleaner route signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserId = Annotated[UUID, Depends(get_current_user_id)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
