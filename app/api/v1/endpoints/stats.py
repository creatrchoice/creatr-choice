"""Stats endpoint for platform statistics."""
from fastapi import APIRouter
from app.services.stats_service import StatsService

router = APIRouter()
service = StatsService()


@router.get(
    "/platform/stats",
    summary="Get Platform Statistics",
    description="Get aggregated counts for free influencers, brands, and collaborations.",
    responses={200: {"description": "Statistics returned successfully"}},
    tags=["platform"]
)
async def get_stats():
    """Get platform-wide statistics."""
    return await service.get_all_stats()
