"""Main API router."""
from fastapi import APIRouter

from app.api.v1.endpoints import influencers

api_router = APIRouter()

api_router.include_router(
    influencers.router,
    prefix="/influencers",
    tags=["influencers"],
)
