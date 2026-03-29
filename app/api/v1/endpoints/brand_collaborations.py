"""Brand collaboration endpoints."""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Body, status
from typing import Optional

from app.schemas.brand_collaboration_schema import (
    CreateCollaborationRequest,
    CollaborationResponse,
    InfluencerListForBrandResponse,
    CollaborationListForInfluencerResponse,
)
from app.services.brand_collaboration_service import BrandCollaborationService


logger = logging.getLogger(__name__)

router = APIRouter()
service = BrandCollaborationService()


@router.get(
    "/brand-collaborations",
    response_model=InfluencerListForBrandResponse,
    summary="Get Brand Collaborations",
    description="Get collaborations filtered by brand_id or influencer_id.",
    responses={
        200: {"description": "List of collaborations"},
        400: {"description": "Missing required parameter"}
    },
    tags=["brand-collaborations"]
)
async def get_collaborations(
    brand_id: Optional[str] = Query(None, description="Get all influencers for this brand"),
    influencer_id: Optional[str] = Query(None, description="Get all brands for this influencer"),
    include_metrics: bool = Query(False, description="Include collaboration metrics"),
):
    cached_time = None
    if brand_id and influencer_id:
        collaboration, was_cached = await service.get_collaboration_by_brand_and_influencer(
            brand_id=brand_id,
            influencer_id=influencer_id,
            include_metrics=include_metrics,
        )
        if not collaboration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No collaboration found between brand_id={brand_id} and influencer_id={influencer_id}"
            )
        return {
            "data": [collaboration],
            "count": 1,
            "brand_id": brand_id,
            "influencer_id": influencer_id,
            "include_metrics": include_metrics,
            "cachedTime": datetime.utcnow().isoformat() if was_cached else None
        }

    if brand_id:
        influencers, was_cached = await service.get_influencers_for_brand(
            brand_id=brand_id,
            include_metrics=include_metrics,
        )
        return {
            "data": influencers,
            "count": len(influencers),
            "brand_id": brand_id,
            "include_metrics": include_metrics,
            "cachedTime": datetime.utcnow().isoformat() if was_cached else None
        }

    if influencer_id:
        collaborations = await service.get_collaborations_for_influencer(influencer_id)
        return {
            "data": collaborations,
            "count": len(collaborations),
            "influencer_id": influencer_id,
            "cachedTime": None
        }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Either brand_id or influencer_id query parameter is required"
    )


@router.post(
    "/brand-collaborations",
    response_model=CollaborationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Brand Collaboration",
    description="Create a new brand-influencer collaboration record with validation.",
    responses={
        201: {"description": "Collaboration created successfully"},
        400: {"description": "Validation error"}
    },
    tags=["brand-collaborations"]
)
async def create_collaboration(request: CreateCollaborationRequest):
    data = request.model_dump()
    try:
        collaboration = await service.create_collaboration(data)
        return collaboration
    except Exception as e:
        logger.error(f"Error creating collaboration: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
