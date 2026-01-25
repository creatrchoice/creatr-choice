# API Documentation

## Overview

The AI Influencer Discovery API provides a comprehensive platform for discovering, analyzing, and managing influencers using advanced AI techniques. The API supports multiple search methods, rich filtering options, and conversational interfaces.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.example.com`

## API Version

Current version: `v1`

All endpoints are prefixed with `/api/v1`

## Interactive Documentation

- **Swagger UI**: `/docs` - Interactive API documentation with "Try it out" functionality
- **ReDoc**: `/redoc` - Alternative API documentation interface
- **OpenAPI JSON**: `/openapi.json` - Machine-readable API specification

## Authentication

Currently, the API does not require authentication. This may change in future versions.

## Rate Limits

Rate limits may apply. Please contact support for enterprise access.

---

## Endpoints

### Root & Health

#### GET `/`

Root endpoint providing API information.

**Response:**
```json
{
  "message": "AI Influencer Discovery API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

#### GET `/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

---

## Influencer Endpoints

### Search Influencers

**GET** `/api/v1/influencers/`

Search and discover influencers based on various criteria.

**Query Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `query` | string | No | Search by name, username, or bio keywords | `fitness` |
| `platform` | string | No | Social media platform | `instagram` |
| `min_followers` | integer | No | Minimum number of followers | `10000` |
| `max_followers` | integer | No | Maximum number of followers | `100000` |
| `category` | string | No | Influencer category/niche | `Fitness` |
| `limit` | integer | No | Number of results (1-100, default: 10) | `10` |
| `offset` | integer | No | Pagination offset (default: 0) | `0` |

**Example Request:**
```bash
GET /api/v1/influencers/?query=fitness&platform=instagram&min_followers=10000&limit=10
```

**Example Response:**
```json
{
  "influencers": [
    {
      "id": "123",
      "username": "johndoe",
      "display_name": "John Doe",
      "platform": "instagram",
      "followers": 50000,
      "following": 1000,
      "posts": 500,
      "profile_image_url": "https://example.com/image.jpg",
      "bio": "Fitness enthusiast",
      "verified": false,
      "category": "Fitness",
      "engagement_rate": 4.5,
      "location": "Mumbai, India",
      "average_views": 5000,
      "profile_url": "https://instagram.com/johndoe"
    }
  ],
  "total": 100,
  "limit": 10,
  "offset": 0,
  "has_more": true,
  "relevance_scores": [0.95, 0.88, 0.82]
}
```

---

### Get Trending Categories

**GET** `/api/v1/influencers/trending/categories`

Get list of currently trending influencer categories.

**Response:**
```json
["Fitness", "Fashion", "Technology", "Food", "Travel"]
```

---

### Get Categories Metadata

**GET** `/api/v1/influencers/categories`

Get comprehensive metadata about all available filter options including categories, cities, creator types, and platforms with statistics.

**Response:**
```json
{
  "interest_categories": [
    {
      "name": "Fitness",
      "count": 500,
      "avg_engagement_rate": 4.5,
      "min_followers": 1000,
      "max_followers": 1000000,
      "avg_followers": 50000
    }
  ],
  "primary_categories": [
    {
      "name": "Lifestyle",
      "count": 300,
      "avg_engagement_rate": 3.8
    }
  ],
  "cities": ["Mumbai", "Delhi", "Bangalore"],
  "creator_types": ["Micro-influencer", "Macro-influencer", "Celebrity"],
  "platforms": ["instagram", "twitter", "youtube"],
  "total_influencers": 10000
}
```

---

### Get Influencer Details

**GET** `/api/v1/influencers/{influencer_id}`

Get detailed information about a specific influencer.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `influencer_id` | string | Yes | Unique identifier for the influencer |

**Example Request:**
```bash
GET /api/v1/influencers/123
```

**Example Response:**
```json
{
  "id": "123",
  "username": "johndoe",
  "display_name": "John Doe",
  "platform": "instagram",
  "followers": 50000,
  "following": 1000,
  "posts": 500,
  "profile_image_url": "https://example.com/image.jpg",
  "bio": "Fitness enthusiast | Personal trainer",
  "verified": false,
  "category": "Fitness",
  "engagement_rate": 4.5,
  "location": "Mumbai, India",
  "average_views": 5000,
  "profile_url": "https://instagram.com/johndoe",
  "average_likes": 2000,
  "average_comments": 150,
  "content_topics": ["Fitness", "Health", "Nutrition"],
  "collaboration_price_range": {
    "min": 5000,
    "max": 15000,
    "currency": "USD"
  },
  "audience_demographics": {
    "age_range": "18-34",
    "gender": {
      "male": 45,
      "female": 55
    }
  }
}
```

**Error Responses:**

- `404 Not Found`: Influencer not found
```json
{
  "detail": "Influencer not found"
}
```

---

### Analyze New Influencer

**POST** `/api/v1/influencers/analyze`

Fetch and analyze a new influencer by their username and platform.

**Request Body:**
```json
{
  "username": "johndoe",
  "platform": "instagram"
}
```

**Supported Platforms:**
- `instagram`
- `twitter`
- `youtube`
- `tiktok`
- `linkedin`

**Example Request:**
```bash
POST /api/v1/influencers/analyze
Content-Type: application/json

{
  "username": "johndoe",
  "platform": "instagram"
}
```

**Response:**
Returns detailed influencer information (same format as Get Influencer Details).

**Error Responses:**

- `404 Not Found`: Influencer not found on the specified platform
```json
{
  "detail": "Influencer 'johndoe' not found on instagram"
}
```

---

### Natural Language Search

**POST** `/api/v1/influencers/search/nlp`

Search for influencers using natural language queries. The AI will understand your intent and extract relevant search parameters automatically.

**Request Body:**
```json
{
  "query": "Find me a fitness micro-influencer in Mumbai who is affordable",
  "limit": 10,
  "offset": 0
}
```

**Example Queries:**
- "Find me a fitness micro-influencer in Mumbai who is affordable"
- "I need Gen-Z fashion creators with high engagement"
- "Show me tech influencers with over 100K followers"
- "Fashion bloggers in Delhi with good engagement rates"
- "Affordable YouTube creators in the gaming niche"

**Example Request:**
```bash
POST /api/v1/influencers/search/nlp
Content-Type: application/json

{
  "query": "Find me a fitness micro-influencer in Mumbai who is affordable",
  "limit": 10
}
```

**Example Response:**
```json
{
  "influencers": [
    {
      "id": "123",
      "username": "johndoe",
      "display_name": "John Doe",
      "platform": "instagram",
      "followers": 50000,
      "relevance_score": 0.95
    }
  ],
  "total": 50,
  "limit": 10,
  "offset": 0,
  "has_more": true,
  "search_time_ms": 250.5
}
```

---

### Hybrid Search

**POST** `/api/v1/influencers/search/hybrid`

Advanced hybrid search combining keyword search, vector similarity search, and explicit filters.

**Request Body:**
```json
{
  "query": "fitness influencer",
  "filters": {
    "platform": "instagram",
    "city": "Mumbai",
    "min_followers": 10000,
    "max_followers": 100000,
    "min_engagement_rate": 3.0,
    "interest_categories": ["Fitness"],
    "creator_type": "Micro-influencer"
  },
  "vector_query": [0.1, 0.2, 0.3, ...],
  "limit": 10,
  "offset": 0
}
```

**Note:** You can use any combination of `query`, `vector_query`, and `filters`. The system will intelligently combine them using Reciprocal Rank Fusion (RRF).

**Example Request:**
```bash
POST /api/v1/influencers/search/hybrid
Content-Type: application/json

{
  "query": "fitness influencer",
  "filters": {
    "platform": "instagram",
    "city": "Mumbai",
    "min_followers": 10000
  },
  "limit": 10
}
```

**Response:**
Same format as Natural Language Search response.

---

### Conversational Search

**POST** `/api/v1/influencers/search/chat`

Chat-like interface for searching influencers with natural conversation flow and refinement support.

**First Query Request:**
```json
{
  "query": "Find fitness influencers in Mumbai",
  "limit": 10,
  "offset": 0
}
```

**Refinement Query Request:**
```json
{
  "query": "Show me only those with more than 100K followers",
  "conversation_id": "conv-abc123",
  "context": {
    "previous_filters": {
      "city": "Mumbai",
      "interest_categories": ["Fitness"]
    },
    "previous_query": "Find fitness influencers in Mumbai"
  },
  "limit": 10
}
```

**Refinement Examples:**
- "Show me only those in Mumbai" → Adds city filter
- "With more than 100K followers" → Adds min_followers filter
- "Only micro-influencers" → Sets creator_type and max_followers
- "With high engagement" → Adds min_engagement_rate filter
- "More affordable" → Decreases max_ppc
- "Add fashion category" → Adds Fashion to interest_categories
- "Remove the location filter" → Removes city filter
- "Show me cheaper options" → Adjusts max_ppc downward

**Example Request:**
```bash
POST /api/v1/influencers/search/chat
Content-Type: application/json

{
  "query": "Find fitness influencers in Mumbai",
  "limit": 10
}
```

**Example Response:**
```json
{
  "influencers": [
    {
      "id": "123",
      "username": "johndoe",
      "relevance_score": 0.88
    }
  ],
  "total": 25,
  "limit": 10,
  "offset": 0,
  "has_more": true,
  "search_time_ms": 320.1,
  "conversation_id": "conv-abc123",
  "applied_filters": {
    "query": "fitness",
    "city": "Mumbai",
    "min_followers": 100000
  },
  "refinement_summary": "Added city filter: Mumbai, Added min_followers: 100000",
  "suggestions": [
    "Filter by engagement rate",
    "Show only verified influencers",
    "Limit to specific platforms"
  ]
}
```

---

## Data Models

### Platform Enum

```typescript
enum Platform {
  TWITTER = "twitter"
  INSTAGRAM = "instagram"
  YOUTUBE = "youtube"
  TIKTOK = "tiktok"
  LINKEDIN = "linkedin"
}
```

### Influencer

Basic influencer information.

```json
{
  "id": "string",
  "username": "string",
  "display_name": "string",
  "platform": "instagram | twitter | youtube | tiktok | linkedin",
  "followers": "integer",
  "following": "integer (optional)",
  "posts": "integer (optional)",
  "profile_image_url": "string (optional)",
  "bio": "string (optional)",
  "verified": "boolean",
  "category": "string (optional)",
  "engagement_rate": "float (optional)",
  "location": "string (optional)",
  "average_views": "integer (optional)",
  "profile_url": "string (optional)"
}
```

### InfluencerDetail

Extended influencer information with additional metrics.

```json
{
  // ... all Influencer fields ...
  "average_likes": "integer (optional)",
  "average_comments": "integer (optional)",
  "recent_posts": "array (optional)",
  "audience_demographics": "object (optional)",
  "content_topics": "array (optional)",
  "collaboration_price_range": "object (optional)",
  "created_at": "datetime (optional)",
  "updated_at": "datetime (optional)"
}
```

### SearchFilters

Available filter options for search queries.

```json
{
  "query": "string (optional)",
  "platform": "string (optional)",
  "min_followers": "integer (optional)",
  "max_followers": "integer (optional)",
  "min_engagement_rate": "float (optional)",
  "max_engagement_rate": "float (optional)",
  "min_avg_views": "integer (optional)",
  "max_avg_views": "integer (optional)",
  "interest_categories": "array (optional)",
  "primary_category": "string (optional)",
  "city": "string (optional)",
  "creator_type": "string (optional)",
  "max_ppc": "integer (optional)",
  "min_ppc": "integer (optional)",
  "language": "string (optional)"
}
```

---

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses follow this format:

```json
{
  "detail": "Error message description"
}
```

---

## Pagination

Most search endpoints support pagination using `limit` and `offset` parameters:

- `limit`: Number of results per page (1-100, default: 10)
- `offset`: Number of results to skip (default: 0)

Response includes:
- `total`: Total number of matching results
- `has_more`: Boolean indicating if more results are available

**Example:**
```bash
# First page
GET /api/v1/influencers/?limit=10&offset=0

# Second page
GET /api/v1/influencers/?limit=10&offset=10
```

---

## Best Practices

1. **Start with Categories**: Use `/api/v1/influencers/categories` to discover available filters before searching
2. **Use Natural Language**: For complex queries, prefer `/search/nlp` over manual filter construction
3. **Conversational Search**: Use `/search/chat` for iterative refinement of search results
4. **Pagination**: Always check `has_more` and use appropriate `limit` values
5. **Error Handling**: Always handle error responses appropriately in your application

---

## Support

For questions, issues, or feature requests, please contact:
- Email: support@example.com
- Documentation: `/docs` (Swagger UI)

---

## Changelog

### Version 1.0.0
- Initial API release
- Basic search functionality
- Natural language search
- Hybrid search
- Conversational search
- Category metadata endpoints
