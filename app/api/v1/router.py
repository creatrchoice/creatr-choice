"""Main API router."""
from fastapi import APIRouter

from app.api.v1.endpoints import influencers, storage

api_router = APIRouter()

api_router.include_router(
    influencers.router,
    prefix="/influencers",
    tags=["influencers"],
)

api_router.include_router(
    storage.router,
    prefix="/storage",
    tags=["storage"],
)
