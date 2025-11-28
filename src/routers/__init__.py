# Routers Package
from src.routers.auth import router as auth_router
from src.routers.users import router as users_router
from src.routers.interests import router as interests_router
from src.routers.digests import router as digests_router

__all__ = ["auth_router", "users_router", "interests_router", "digests_router"]
