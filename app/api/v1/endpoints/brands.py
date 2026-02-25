"""Brand endpoints."""
import logging
from fastapi import APIRouter, HTTPException, Query, Body, status
from typing import Optional

from app.schemas.brand_schema import (
    CreateBrandRequest,
    UpdateBrandRequest,
    BrandResponse,
    BrandListResponse,
)
from app.services.brand_service import BrandService


logger = logging.getLogger(__name__)

router = APIRouter()
service = BrandService()


@router.get(
    "/",
    response_model=BrandListResponse,
    summary="Get Brands",
    description="Get all brands with pagination using size and offset parameters.",
    responses={
        200: {"description": "List of brands"},
        404: {"description": "Brand not found"}
    },
    tags=["brands"]
)
async def get_brands(
    id: Optional[str] = Query(None, description="Filter by brand ID"),
    name: Optional[str] = Query(None, description="Filter by brand name"),
    size: int = Query(20, ge=1, le=1000, description="Number of brands to return"),
    offset: int = Query(0, ge=0, description="Number of brands to skip"),
):
    if id:
        brand = await service.get_brand_by_id(id)
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        return {
            "data": [brand],
            "count": 1,
            "offset": None
        }

    if name:
        brand = await service.get_brand_by_name(name)
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        return {
            "data": [brand],
            "count": 1,
            "offset": None
        }

    brands, next_offset = await service.list_brands(limit=size, cursor=str(offset), offset=offset)
    return {
        "data": brands,
        "count": len(brands),
        "offset": next_offset
    }


@router.post(
    "/",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Brand",
    description="Create a new brand record with validation.",
    responses={
        201: {"description": "Brand created successfully"},
        400: {"description": "Validation error"}
    },
    tags=["brands"]
)
async def create_brand(request: CreateBrandRequest):
    data = request.model_dump()
    try:
        brand = await service.create_brand(data)
        return brand
    except Exception as e:
        logger.error(f"Error creating brand: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{brand_id}",
    response_model=BrandResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Brand",
    description="Update an existing brand (partial update).",
    responses={
        200: {"description": "Brand updated successfully"},
        404: {"description": "Brand not found"}
    },
    tags=["brands"]
)
async def update_brand(brand_id: str, request: UpdateBrandRequest):
    """Update an existing brand by its ID (partial update)."""
    data = request.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    try:
        brand = await service.update_brand(brand_id, data)
        return brand
    except Exception as e:
        logger.error(f"Error updating brand: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{brand_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Brand",
    description="Delete a brand by ID.",
    responses={
        200: {"description": "Brand deleted successfully"},
        404: {"description": "Brand not found"}
    },
    tags=["brands"]
)
async def delete_brand(brand_id: str):
    """Delete a brand by its ID."""
    try:
        await service.delete_brand(brand_id)
        return {"message": f"Brand '{brand_id}' deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting brand: {e}")
        if "Resource Not Found" in str(e) or "NotFound" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
