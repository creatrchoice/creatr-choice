"""Admin endpoints for queue management."""
import os
import logging
from fastapi import APIRouter, Body, Header, HTTPException, status

from app.services.queue_service import queue_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


class AddBrandRequest:
    """Request body for adding brand to queue."""
    brand: str
    max_posts: int = 10000
    max_api_calls: int = 500


@router.post(
    "/queue/add-brand",
    status_code=status.HTTP_201_CREATED,
    summary="Add brand to sync queue",
    description="Add a brand to the background worker queue for influencer sync processing"
)
async def add_brand_to_queue(
    brand: str = Body(..., description="Brand Instagram username (without @)", example="mamaearth"),
    max_posts: int = Body(10000, description="Maximum posts to fetch", ge=1, le=100000),
    max_api_calls: int = Body(500, description="Maximum API calls to make", ge=1, le=5000),
    admin_key: str = Header(..., alias="ADMIN_KEY", description="Admin API key for authentication")
):
    """Add a brand to the sync queue."""
    
    # Validate admin key
    expected_key = os.getenv("ADMIN_KEY")
    if not expected_key:
        logger.error("ADMIN_KEY not configured on server")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin key not configured"
        )
    
    if admin_key != expected_key:
        logger.warning(f"Invalid admin key attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key"
        )

    # Validate brand parameter
    if not brand or not brand.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brand cannot be empty"
        )

    # Add job to queue
    job_id = queue_service.add_brand_job(
        brand=brand.strip(),
        max_posts=max_posts,
        max_api_calls=max_api_calls
    )

    logger.info(f"Job {job_id} queued for brand @{brand}")

    return {
        "status": "queued",
        "job_id": job_id,
        "brand": brand,
        "max_posts": max_posts,
        "max_api_calls": max_api_calls
    }