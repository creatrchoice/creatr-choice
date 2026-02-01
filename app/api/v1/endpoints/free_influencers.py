"""Free influencer endpoints."""
import logging
from fastapi import APIRouter, HTTPException, Query, Body, status
from typing import Optional

from app.schemas.free_influencer_schema import (
    CreateInfluencerRequest,
    InfluencerResponse,
    InfluencerListResponse,
)
from app.services.free_influencer_service import FreeInfluencerService


logger = logging.getLogger(__name__)

router = APIRouter()
service = FreeInfluencerService()


@router.get(
    "/free-influencers",
    response_model=InfluencerListResponse,
    summary="Get Free Influencers",
    description="Get all free influencers or filter by id, username, platform, categories, or location.",
    responses={
        200: {"description": "List of influencers"},
        404: {"description": "Influencer not found"}
    },
    tags=["free-influencers"]
)
async def get_influencers(
    id: Optional[str] = Query(None, description="Filter by influencer ID"),
    username: Optional[str] = Query(None, description="Filter by username"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    location: Optional[str] = Query(None, description="Filter by location"),
):
    if id:
        influencer = await service.get_influencer_by_id(id, platform)
        if not influencer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Influencer not found")
        return {
            "data": [influencer],
            "count": 1
        }

    if username:
        influencer = await service.get_influencer_by_username(username, platform)
        if not influencer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Influencer not found")
        return {
            "data": [influencer],
            "count": 1
        }

    categories_list = None
    if categories:
        categories_list = [c.strip() for c in categories.split(",")]

    influencers = await service.list_influencers(
        platform=platform,
        categories=categories_list,
        location=location,
    )
    return {
        "data": influencers,
        "count": len(influencers)
    }


@router.post(
    "/free-influencers",
    response_model=InfluencerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Free Influencer",
    description="Create a new free influencer record with validation.",
    responses={
        201: {"description": "Influencer created successfully"},
        400: {"description": "Validation error"}
    },
    tags=["free-influencers"]
)
async def create_influencer(request: CreateInfluencerRequest):
    data = request.model_dump()
    try:
        influencer = await service.create_influencer(data)
        return influencer
    except Exception as e:
        logger.error(f"Error creating influencer: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
