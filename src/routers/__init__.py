# Routers Package
from src.routers.auth import router as auth_router
from src.routers.digests import router as digests_router
from src.routers.health import router as health_router
from src.routers.interests import router as interests_router
from src.routers.users import router as users_router

__all__ = [
    "auth_router",
    "digests_router",
    "health_router",
    "interests_router",
    "users_router",
]
