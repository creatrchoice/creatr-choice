"""Main API router."""
from fastapi import APIRouter

from app.api.v1.endpoints import influencers, storage, creators, free_influencers, brands, brand_collaborations

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

api_router.include_router(
    creators.router,
    prefix="/creators",
    tags=["creators"],
)

api_router.include_router(
    free_influencers.router,
    prefix="/free-influencers",
    tags=["free-influencers"],
)

api_router.include_router(
    brands.router,
    prefix="/brands",
    tags=["brands"],
)

api_router.include_router(
    brand_collaborations.router,
    prefix="",
    tags=["brand-collaborations"],
)
