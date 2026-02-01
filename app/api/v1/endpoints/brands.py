"""Brand endpoints."""
import logging
from fastapi import APIRouter, HTTPException, Query, Body, status
from typing import Optional

from app.schemas.brand_schema import (
    CreateBrandRequest,
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
    description="Get all brands or filter by id or name.",
    responses={
        200: {"description": "List of brands"},
        404: {"description": "Brand not found"}
    },
    tags=["brands"]
)
async def get_brands(
    id: Optional[str] = Query(None, description="Filter by brand ID"),
    name: Optional[str] = Query(None, description="Filter by brand name"),
):
    if id:
        brand = await service.get_brand_by_id(id)
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        return {
            "data": [brand],
            "count": 1
        }

    if name:
        brand = await service.get_brand_by_name(name)
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        return {
            "data": [brand],
            "count": 1
        }

    brands = await service.list_brands()
    return {
        "data": brands,
        "count": len(brands)
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
