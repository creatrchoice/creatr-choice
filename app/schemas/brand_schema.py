"""Brand schemas - request (validated) and response (documented only)."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List


class CreateBrandRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_.\-]+$",
                    description="Unique brand identifier", example="brand.123")
    name: str = Field(..., min_length=1, max_length=200,
                      description="Brand name", example="Nike")
    logo: Optional[str] = Field(None, max_length=500, description="Logo URL")
    description: Optional[str] = Field(None, max_length=1000, description="Brand description")
    categories: Optional[List[str]] = Field(None, max_length=20, description="Brand categories")
    instaHandle: Optional[str] = Field(None, max_length=100, description="Instagram handle")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "brand_123",
            "name": "Nike",
            "logo": "https://example.com/logo.png",
            "description": "Sportswear brand",
            "categories": ["sports", "fitness"]
        }
    })


class UpdateBrandRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200,
                                description="Brand name", example="Nike")
    logo: Optional[str] = Field(None, max_length=500, description="Logo URL")
    description: Optional[str] = Field(None, max_length=1000, description="Brand description")
    categories: Optional[List[str]] = Field(None, max_length=20, description="Brand categories")
    instaHandle: Optional[str] = Field(None, max_length=100, description="Instagram handle")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Nike Updated",
            "logo": "https://example.com/new-logo.png",
            "description": "Updated sportswear brand"
        }
    })


class BrandResponse(BaseModel):
    id: str
    name: str
    logo: Optional[str] = None
    description: Optional[str] = None
    categories: Optional[List[str]] = None
    instaHandle: Optional[str] = None

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
        "example": {
            "id": "brand_123",
            "name": "Nike",
            "logo": "https://example.com/logo.png",
            "description": "Sportswear brand",
            "categories": ["sports", "fitness"]
        }
    })


class BrandListResponse(BaseModel):
    data: List[BrandResponse]
    count: int

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
        "example": {
            "data": [{"id": "brand_1", "name": "Nike"}, {"id": "brand_2", "name": "Adidas"}],
            "count": 2
        }
    })
