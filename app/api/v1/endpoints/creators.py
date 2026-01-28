"""Creator data endpoints for fetching influencer data from Google Sheets."""
import logging
import json
import csv
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
import aiohttp

logger = logging.getLogger(__name__)

router = APIRouter()

SHEET_MAPPING_PATH = Path(__file__).parent.parent.parent.parent / "config" / "infl-data-sheet.json"

def load_sheet_mapping() -> Dict[str, Any]:
    """Load the Google Sheet ID mapping from config."""
    try:
        with open(SHEET_MAPPING_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load sheet mapping: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load sheet configuration"
        )


def parse_number_string(value: str) -> int:
    """Parse strings like '2.5M' or '100K' into integers.

    Args:
        value: String representation of a number (e.g., "2.5M", "100K", "1500")

    Returns:
        Integer value
    """
    if not value or not isinstance(value, str):
        return 0

    value = value.strip().upper()

    value = value.replace(",", "")

    try:
        if "M" in value:
            number = float(value.replace("M", ""))
            return int(number * 1_000_000)

        elif "K" in value:
            number = float(value.replace("K", ""))
            return int(number * 1_000)

        elif "B" in value:
            number = float(value.replace("B", ""))
            return int(number * 1_000_000_000)

        else:
            return int(float(value))

    except (ValueError, TypeError):
        logger.warning(f"Could not parse number string: {value}")
        return 0


class InfluencerStats(BaseModel):
    """Statistics about influencers."""
    total_creators: int = Field(..., description="Total number of creators")
    total_likes: int = Field(..., description="Sum of all likes")
    avg_likes: int = Field(..., description="Average likes per creator")


class CreatorInfluencersResponse(BaseModel):
    """Response model for creator influencers endpoint."""
    stats: InfluencerStats = Field(..., description="Aggregated statistics")
    influencers: List[Dict[str, Any]] = Field(..., description="List of influencer data")

    class Config:
        json_schema_extra = {
            "example": {
                "stats": {
                    "total_creators": 156,
                    "total_likes": 45600000,
                    "avg_likes": 292307
                },
                "influencers": [
                    {
                        "Name": "Jane Doe",
                        "Followers": "50K",
                        "Likes": "2.5M",
                        "Platform": "Instagram"
                    }
                ]
            }
        }


@router.get(
    "/influencers",
    response_model=CreatorInfluencersResponse,
    summary="Get Brand Influencers from Google Sheets",
    description="Fetches influencer data for a specific brand from Google Sheets and calculates statistics.",
    responses={
        200: {
            "description": "Successfully fetched influencer data",
        },
        400: {
            "description": "Invalid brand name or missing brand parameter",
        },
        404: {
            "description": "Brand not found in sheet mapping",
        },
        500: {
            "description": "Failed to fetch or parse data from Google Sheets",
        }
    },
    tags=["creators"]
)
async def get_brand_influencers(
    brand: str = Query(..., description="Brand name to fetch influencers for", example="Nykaa")
) -> CreatorInfluencersResponse:
    """
    Fetch influencer data for a specific brand from Google Sheets.

    This endpoint:
    1. Takes a brand name as a query parameter
    2. Looks up the Google Sheet ID from the config mapping
    3. Fetches CSV data from Google Sheets
    4. Parses the data into a list of influencer objects
    5. Calculates statistics (total creators, total likes, average likes)
    6. Returns both the stats and the influencer data

    Args:
        brand: Name of the brand (must exist in the sheet mapping)

    Returns:
        CreatorInfluencersResponse with stats and influencer list
    """
    try:
        sheet_mapping = load_sheet_mapping()

        if brand not in sheet_mapping.get("brands", {}):
            available_brands = list(sheet_mapping.get("brands", {}).keys())
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Brand '{brand}' not found. Available brands: {', '.join(available_brands)}"
            )

        brand_data = sheet_mapping["brands"][brand]
        sheet_id = brand_data["sheet_id"]

        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

        logger.info(f"Fetching influencer data for brand '{brand}' from sheet {sheet_id}")

        timeout = aiohttp.ClientTimeout(total=30.0)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(csv_url) as response:
                response.raise_for_status()
                csv_content = await response.text()

        csv_reader = csv.DictReader(csv_content.splitlines())
        influencers = list(csv_reader)

        if not influencers:
            logger.warning(f"No influencer data found for brand '{brand}'")
            return CreatorInfluencersResponse(
                stats=InfluencerStats(
                    total_creators=0,
                    total_likes=0,
                    avg_likes=0
                ),
                influencers=[]
            )

        total_creators = len(influencers)
        total_likes = 0

        likes_column = None
        first_row = influencers[0] if influencers else {}
        for key in first_row.keys():
            if key.lower() == "likes":
                likes_column = key
                break

        if likes_column:
            for influencer in influencers:
                likes_value = influencer.get(likes_column, "0")
                total_likes += parse_number_string(likes_value)
        else:
            logger.warning(f"No 'Likes' column found in the sheet for brand '{brand}'")

        avg_likes = total_likes // total_creators if total_creators > 0 else 0

        logger.info(
            f"Successfully fetched {total_creators} influencers for brand '{brand}' "
            f"(total_likes: {total_likes}, avg_likes: {avg_likes})"
        )

        return CreatorInfluencersResponse(
            stats=InfluencerStats(
                total_creators=total_creators,
                total_likes=total_likes,
                avg_likes=avg_likes
            ),
            influencers=influencers
        )

    except HTTPException:
        raise

    except aiohttp.ClientResponseError as e:
        logger.error(f"HTTP error fetching sheet data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch data from Google Sheets: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Error in get_brand_influencers: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process influencer data: {str(e)}"
        )
