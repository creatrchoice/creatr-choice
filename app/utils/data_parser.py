"""Data parsing and normalization utilities."""
import re
from typing import Any, Dict, Optional
from datetime import datetime
from app.models.influencer_data import InfluencerData


def parse_display_number(value: str) -> Optional[int]:
    """
    Parse display numbers like "973.5 K" or "1.2 M" to integers.
    
    Args:
        value: String like "973.5 K", "1.2 M", "500"
    
    Returns:
        Integer value or None if parsing fails
    """
    if not value or not isinstance(value, str):
        return None
    
    # Remove whitespace and convert to lowercase
    value = value.strip().lower()
    
    # Handle empty strings
    if not value or value == "n/a" or value == "null":
        return None
    
    # Extract number and multiplier
    match = re.match(r"([\d.]+)\s*([kmb]?)", value)
    if not match:
        # Try to parse as plain number
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    number_str, multiplier = match.groups()
    try:
        number = float(number_str)
    except (ValueError, TypeError):
        return None
    
    # Apply multiplier
    multiplier_map = {
        "k": 1000,
        "m": 1000000,
        "b": 1000000000,
    }
    
    multiplier_value = multiplier_map.get(multiplier, 1)
    return int(number * multiplier_value)


def parse_percentage(value: str) -> Optional[float]:
    """
    Parse percentage strings like "4.88%" to float.
    
    Args:
        value: String like "4.88%"
    
    Returns:
        Float value or None if parsing fails
    """
    if not value or not isinstance(value, str):
        return None
    
    value = value.strip().lower()
    if not value or value == "n/a" or value == "null":
        return None
    
    # Remove % sign and parse
    value = value.replace("%", "").strip()
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_date(value: Any) -> Optional[datetime]:
    """
    Parse date from various formats including MongoDB $date format.
    
    Args:
        value: Date value (datetime, dict with $date, or ISO string)
    
    Returns:
        datetime object or None
    """
    if value is None:
        return None
    
    if isinstance(value, datetime):
        return value
    
    if isinstance(value, dict) and "$date" in value:
        # MongoDB date format: {"$date": "2026-01-09T19:23:36.353Z"}
        date_str = value["$date"]
        try:
            # Handle ISO format with Z
            if date_str.endswith("Z"):
                date_str = date_str[:-1] + "+00:00"
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    
    if isinstance(value, str):
        try:
            # Try ISO format
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    
    return None


def normalize_influencer_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize influencer data from MongoDB format.
    
    Args:
        data: Raw dictionary from MongoDB
    
    Returns:
        Normalized dictionary ready for Pydantic model
    """
    normalized = data.copy()
    
    # Normalize display values to counts
    if "followers" in normalized and isinstance(normalized["followers"], str):
        normalized["followers_count"] = parse_display_number(normalized["followers"])
    
    if "avg_views" in normalized and isinstance(normalized["avg_views"], str):
        normalized["avg_views_count"] = parse_display_number(normalized["avg_views"])
    
    if "engagement_rate" in normalized and isinstance(normalized["engagement_rate"], str):
        normalized["engagement_rate_value"] = parse_percentage(normalized["engagement_rate"])
    
    # Normalize dates
    if "fetched_at" in normalized:
        normalized["fetched_at"] = parse_date(normalized["fetched_at"])
    
    if "processed_at" in normalized:
        normalized["processed_at"] = parse_date(normalized["processed_at"])
    
    # Ensure interest_categories is a list of strings
    if "interest_categories" in normalized:
        if isinstance(normalized["interest_categories"], list):
            # Filter out None values and ensure strings
            normalized["interest_categories"] = [
                str(cat) for cat in normalized["interest_categories"] if cat
            ]
        else:
            normalized["interest_categories"] = []
    
    # Ensure interests list is properly formatted
    if "interests" in normalized and isinstance(normalized["interests"], list):
        # Keep as is, Pydantic will validate
        pass
    
    # Ensure primary_category is properly formatted
    if "primary_category" in normalized:
        if isinstance(normalized["primary_category"], dict):
            # Keep as is
            pass
        elif isinstance(normalized["primary_category"], str):
            # Convert string to dict
            normalized["primary_category"] = {"name": normalized["primary_category"]}
        elif normalized["primary_category"] is None:
            normalized["primary_category"] = None
    
    return normalized


def validate_influencer_data(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate influencer data before migration.
    
    Args:
        data: Normalized influencer data
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Required fields (username is optional, we'll generate it if missing)
    required_fields = ["id", "influencer_id", "name", "platform"]
    for field in required_fields:
        if field not in data or data[field] is None:
            return False, f"Missing required field: {field}"
    
    # Generate username if missing
    if "username" not in data or not data["username"]:
        # Try to extract from URL or generate from name/id
        if "url" in data and data["url"]:
            # Extract username from Instagram URL
            import re
            match = re.search(r"instagram\.com/([^/?]+)", data["url"])
            if match:
                data["username"] = match.group(1)
            else:
                # Generate from name or use id
                name = data.get("name", "").lower().replace(" ", "_")
                data["username"] = f"user_{data.get('id', 'unknown')}" if not name else name[:50]
        else:
            # Generate from name or use id
            name = data.get("name", "").lower().replace(" ", "_")
            data["username"] = f"user_{data.get('id', 'unknown')}" if not name else name[:50]
    
    # Validate platform
    valid_platforms = ["instagram", "twitter", "youtube", "tiktok", "linkedin"]
    if data.get("platform") not in valid_platforms:
        return False, f"Invalid platform: {data.get('platform')}"
    
    # Validate numeric fields if present
    numeric_fields = ["followers_count", "engagement_rate_value", "ppc"]
    for field in numeric_fields:
        if field in data and data[field] is not None:
            if not isinstance(data[field], (int, float)):
                return False, f"Invalid type for {field}: expected number"
    
    return True, None
