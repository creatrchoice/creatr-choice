# AI Influencer Discovery API Documentation

## Base URL
```
http://localhost:8000
```

## API Version
```
/api/v1
```

## Authentication
Currently, no authentication is required. In production, add API keys or OAuth.

---

## Table of Contents
1. [Health Check](#health-check)
2. [Basic Search](#basic-search)
3. [Get Influencer by ID](#get-influencer-by-id)
4. [Natural Language Search (NLP)](#natural-language-search-nlp)
5. [Hybrid Search](#hybrid-search)
6. [Conversational Search (Chat)](#conversational-search-chat)
7. [Get Categories](#get-categories)
8. [Get Trending Categories](#get-trending-categories)
9. [Response Models](#response-models)

---

## Health Check

### GET `/health`

Check if the API server is running.

**Response:**
```json
{
  "status": "healthy"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

## Basic Search

### GET `/api/v1/influencers/`

Search influencers using query parameters.

**Query Parameters:**
- `query` (optional, string): Search query for name, username, or bio keywords
- `platform` (optional, string): Filter by platform (instagram, twitter, youtube)
- `min_followers` (optional, int): Minimum number of followers
- `max_followers` (optional, int): Maximum number of followers
- `category` (optional, string): Filter by influencer category/niche
- `limit` (optional, int, default: 10): Number of results (1-100)
- `offset` (optional, int, default: 0): Pagination offset

**Example:**
```bash
curl "http://localhost:8000/api/v1/influencers/?query=fitness&platform=instagram&min_followers=100000&limit=10"
```

**Response:**
```json
{
  "influencers": [
    {
      "id": "84739",
      "username": "simpletipsanwesha",
      "display_name": "Anwesha Mukherjee Sarkar",
      "platform": "instagram",
      "followers": 100100,
      "following": null,
      "posts": null,
      "profile_image_url": "https://influencer-media.s3.ap-south-1.amazonaws.com/1265762972",
      "bio": null,
      "verified": false,
      "category": "Fashion",
      "engagement_rate": 0.65,
      "location": "kolkata",
      "average_views": 23900,
      "profile_url": "https://www.instagram.com/simpletipsanwesha"
    }
  ],
  "total": 1000,
  "limit": 10,
  "offset": 0,
  "has_more": true,
  "relevance_scores": [1.0, 0.95, 0.90]
}
```

---

## Get Influencer by ID

### GET `/api/v1/influencers/{influencer_id}`

Get detailed information about a specific influencer.

**Path Parameters:**
- `influencer_id` (string, required): Unique identifier for the influencer

**Example:**
```bash
curl http://localhost:8000/api/v1/influencers/84739
```

**Response:**
```json
{
  "id": "84739",
  "username": "simpletipsanwesha",
  "display_name": "Anwesha Mukherjee Sarkar",
  "platform": "instagram",
  "followers": 100100,
  "following": null,
  "posts": null,
  "profile_image_url": "https://influencer-media.s3.ap-south-1.amazonaws.com/1265762972",
  "bio": null,
  "verified": false,
  "category": "Fashion",
  "engagement_rate": 0.65,
  "location": "kolkata",
  "average_views": 23900,
  "profile_url": "https://www.instagram.com/simpletipsanwesha",
  "content_topics": ["Fashion", "Lifestyle"],
  "average_likes": null,
  "average_comments": null,
  "recent_posts": null,
  "audience_demographics": null,
  "collaboration_price_range": null,
  "created_at": null,
  "updated_at": null
}
```

---

## Natural Language Search (NLP)

### POST `/api/v1/influencers/search/nlp`

Search influencers using natural language queries. The AI understands your intent and extracts search parameters automatically.

**Request Body:**
```json
{
  "query": "Find fitness influencers in Mumbai with high engagement",
  "limit": 10,
  "offset": 0
}
```

**Fields:**
- `query` (string, required): Natural language search query
- `limit` (int, optional, default: 10): Number of results (1-100)
- `offset` (int, optional, default: 0): Pagination offset

**Example Queries:**
- "Find fitness influencers in Mumbai"
- "Show me fashion micro-influencers with over 100K followers"
- "I need tech creators with high engagement rates"
- "Find affordable beauty influencers in Delhi"

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/influencers/search/nlp" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find fitness influencers in Mumbai with high engagement",
    "limit": 5
  }'
```

**Response:**
```json
{
  "influencers": [
    {
      "id": "194342",
      "username": "loki_mannnnn",
      "display_name": "LOGESH | Fitness instructor & Speaker |",
      "platform": "instagram",
      "followers": 332300,
      "category": "Fitness",
      "engagement_rate": 14.35,
      "location": "other",
      "average_views": 473300,
      "profile_url": "https://www.instagram.com/loki_mannnnn",
      "relevance_score": 0.032522473484277725
    }
  ],
  "total": 263,
  "limit": 5,
  "offset": 0,
  "has_more": true,
  "search_time_ms": 407.6087474822998
}
```

**How It Works:**
1. AI analyzes your natural language query
2. Extracts filters (category, city, followers, engagement, etc.)
3. Generates embedding for semantic search
4. Performs hybrid search (keyword + vector + filters)
5. Returns ranked results with relevance scores

---

## Hybrid Search

### POST `/api/v1/influencers/search/hybrid`

Advanced hybrid search combining keyword, vector, and explicit filters.

**Request Body:**
```json
{
  "query": "fitness trainer",
  "filters": {
    "platform": "instagram",
    "city": "Mumbai",
    "min_followers": 100000,
    "max_followers": 1000000,
    "min_engagement_rate": 3.0,
    "interest_categories": ["Fitness", "Health"],
    "creator_type": "micro"
  },
  "limit": 10,
  "offset": 0
}
```

**Fields:**
- `query` (string, optional): Keyword search query
- `filters` (object, optional): Explicit search filters
  - `platform` (string): Platform filter
  - `city` (string): City filter
  - `min_followers` (int): Minimum followers
  - `max_followers` (int): Maximum followers
  - `min_engagement_rate` (float): Minimum engagement rate
  - `max_engagement_rate` (float): Maximum engagement rate
  - `min_avg_views` (int): Minimum average views
  - `max_avg_views` (int): Maximum average views
  - `interest_categories` (array): List of interest categories
  - `primary_category` (string): Primary category
  - `creator_type` (string): Creator type (macro, micro, nano)
  - `min_ppc` (int): Minimum price per collaboration
  - `max_ppc` (int): Maximum price per collaboration
- `limit` (int, optional, default: 10): Number of results
- `offset` (int, optional, default: 0): Pagination offset

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/influencers/search/hybrid" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "fitness",
    "filters": {
      "city": "Mumbai",
      "min_followers": 100000,
      "min_engagement_rate": 3.0
    },
    "limit": 10
  }'
```

**Response:**
Same as NLP Search response format.

---

## Conversational Search (Chat)

### POST `/api/v1/influencers/search/chat`

Chat-like interface for refining search results through conversation. Maintains context across multiple queries.

**First Query Request:**
```json
{
  "query": "Find fashion influencers in Mumbai",
  "limit": 10
}
```

**Refinement Query Request:**
```json
{
  "query": "Show me only those with more than 100K followers",
  "conversation_id": "5c6fc5a2-f3b0-4aac-bfc7-4bf150548d34",
  "limit": 10
}
```

**Fields:**
- `query` (string, required): Natural language query or refinement
- `conversation_id` (string, optional): Conversation ID from previous response (for refinements)
- `context` (object, optional): Previous conversation context (auto-managed)
- `limit` (int, optional, default: 10): Number of results

**Example - First Query:**
```bash
curl -X POST "http://localhost:8000/api/v1/influencers/search/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find tech influencers",
    "limit": 5
  }'
```

**First Query Response:**
```json
{
  "influencers": [...],
  "total": 82,
  "limit": 5,
  "offset": 0,
  "has_more": true,
  "search_time_ms": 1527.097225189209,
  "conversation_id": "5c6fc5a2-f3b0-4aac-bfc7-4bf150548d34",
  "applied_filters": {
    "interest_categories": ["Gadget Review"]
  },
  "refinement_summary": null,
  "suggestions": [
    "Narrow down by city or category",
    "Add minimum followers requirement",
    "Filter by specific city"
  ]
}
```

**Example - Refinement Query:**
```bash
curl -X POST "http://localhost:8000/api/v1/influencers/search/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me only those in Mumbai",
    "conversation_id": "5c6fc5a2-f3b0-4aac-bfc7-4bf150548d34",
    "limit": 5
  }'
```

**Refinement Response:**
```json
{
  "influencers": [...],
  "total": 3,
  "limit": 5,
  "offset": 0,
  "has_more": false,
  "search_time_ms": 327.49104499816895,
  "conversation_id": "5c6fc5a2-f3b0-4aac-bfc7-4bf150548d34",
  "applied_filters": {
    "interest_categories": ["Fashion"],
    "city": "Mumbai"
  },
  "refinement_summary": "Refined search: filtered by city: Mumbai",
  "suggestions": [
    "Show only high engagement influencers",
    "Filter by budget/price range"
  ]
}
```

**Refinement Examples:**
- "Show me only those in Mumbai" → Adds city filter
- "With more than 100K followers" → Adds min_followers filter
- "Only micro-influencers" → Sets creator_type and max_followers
- "With high engagement" → Adds min_engagement_rate filter
- "More affordable" → Decreases max_ppc
- "Add fashion category" → Adds Fashion to interest_categories

**How It Works:**
1. First query: Analyzes query, extracts filters, performs search
2. Returns conversation_id and applied_filters
3. Refinement query: Uses conversation_id to merge new filters with previous ones
4. Maintains context across the conversation
5. Provides refinement summary and suggestions

---

## Get Categories

### GET `/api/v1/influencers/categories`

Get all available categories, cities, creator types, and platforms with statistics.

**Example:**
```bash
curl http://localhost:8000/api/v1/influencers/categories
```

**Response:**
```json
{
  "interest_categories": [
    {
      "name": "Fashion",
      "count": 1250,
      "avg_engagement_rate": 4.5,
      "avg_followers": 500000,
      "min_followers": 10000,
      "max_followers": 5000000
    },
    {
      "name": "Fitness",
      "count": 890,
      "avg_engagement_rate": 5.2,
      "avg_followers": 350000,
      "min_followers": 5000,
      "max_followers": 3000000
    }
  ],
  "primary_categories": [
    {
      "name": "Fashion",
      "count": 850,
      "avg_engagement_rate": 4.3
    }
  ],
  "cities": ["Mumbai", "Delhi", "Bangalore", "Kolkata", "Chennai"],
  "creator_types": ["macro", "micro", "nano"],
  "platforms": ["instagram", "twitter", "youtube"],
  "total_influencers": 198514
}
```

---

## Get Trending Categories

### GET `/api/v1/influencers/trending/categories`

Get list of top 10 trending influencer categories by count.

**Example:**
```bash
curl http://localhost:8000/api/v1/influencers/trending/categories
```

**Response:**
```json
[
  "Fashion",
  "Lifestyle",
  "Fitness",
  "Beauty",
  "Food",
  "Travel",
  "Tech",
  "Business",
  "Entertainment",
  "Sports"
]
```

---

## Response Models

### Influencer
```json
{
  "id": "string",
  "username": "string",
  "display_name": "string",
  "platform": "instagram | twitter | youtube",
  "followers": 0,
  "following": null,
  "posts": null,
  "profile_image_url": "string | null",
  "bio": "string | null",
  "verified": false,
  "category": "string | null",
  "engagement_rate": 0.0,
  "location": "string | null",
  "average_views": 0,
  "profile_url": "string | null"
}
```

### InfluencerDetail (extends Influencer)
```json
{
  ...Influencer fields,
  "average_likes": 0,
  "average_comments": 0,
  "recent_posts": [],
  "audience_demographics": {},
  "content_topics": [],
  "collaboration_price_range": {},
  "created_at": "datetime | null",
  "updated_at": "datetime | null"
}
```

### Search Response
```json
{
  "influencers": [Influencer],
  "total": 0,
  "limit": 10,
  "offset": 0,
  "has_more": false,
  "relevance_scores": [0.0],
  "search_time_ms": 0.0
}
```

### Chat Search Response (extends Search Response)
```json
{
  ...Search Response fields,
  "conversation_id": "uuid",
  "applied_filters": {
    "query": null,
    "platform": null,
    "min_followers": null,
    "max_followers": null,
    "min_engagement_rate": null,
    "max_engagement_rate": null,
    "min_avg_views": null,
    "max_avg_views": null,
    "interest_categories": [],
    "primary_category": null,
    "city": null,
    "creator_type": null,
    "max_ppc": null,
    "min_ppc": null,
    "language": null
  },
  "refinement_summary": "string | null",
  "suggestions": []
}
```

---

## Database Storage Details

### Azure Cosmos DB (NoSQL)
**Stores:** Complete metadata (all fields) - **NO embeddings**

**Key Fields:**
- Identifiers: `id`, `influencer_id`, `username`, `name`
- Platform & Location: `platform`, `city`, `location`, `language`
- Followers & Engagement: `followers_count`, `engagement_rate_value`, `engagements_count`
- Views: `avg_views_count`
- Categories: `interest_categories`, `primary_category`, `creator_type`
- Pricing: `ppc`, `speed_score`
- Profile: `url`, `picture`
- Metadata: `fetched_at`, `processed_at`, `prediction`

**Partition Key:** `platform`

### Azure AI Search
**Stores:** Searchable metadata + **embeddings** (3072 dimensions)

**Key Fields:**
- Searchable: `name`, `username`
- Filterable: `platform`, `city`, `creator_type`, `followers_count`, `engagement_rate_value`, `avg_views_count`
- Facetable: `platform`, `city`, `creator_type`, `interest_categories`, `primary_category`
- Vector: `embedding` (3072 dimensions for semantic search)

**Purpose:** Fast hybrid search (keyword + vector + filters)

---

## Error Responses

### 404 Not Found
```json
{
  "detail": "Influencer not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. In production, add rate limiting based on API keys.

---

## Interactive API Documentation

Visit the interactive API documentation:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Example Workflows

### Workflow 1: Find Fitness Influencers
```bash
# Step 1: Natural language search
curl -X POST "http://localhost:8000/api/v1/influencers/search/nlp" \
  -H "Content-Type: application/json" \
  -d '{"query": "Find fitness influencers in Mumbai", "limit": 10}'

# Step 2: Get details of a specific influencer
curl "http://localhost:8000/api/v1/influencers/194342"
```

### Workflow 2: Conversational Refinement
```bash
# Step 1: Initial search
RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/influencers/search/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Find fashion influencers", "limit": 10}')

# Extract conversation_id
CONV_ID=$(echo $RESPONSE | jq -r '.conversation_id')

# Step 2: Refine search
curl -X POST "http://localhost:8000/api/v1/influencers/search/chat" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Show me only those in Mumbai\", \"conversation_id\": \"$CONV_ID\", \"limit\": 10}"

# Step 3: Further refinement
curl -X POST "http://localhost:8000/api/v1/influencers/search/chat" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"With more than 100K followers\", \"conversation_id\": \"$CONV_ID\", \"limit\": 10}"
```

### Workflow 3: Get Available Categories
```bash
# Get all categories for building filters
curl "http://localhost:8000/api/v1/influencers/categories" | jq '.interest_categories[].name'

# Get trending categories
curl "http://localhost:8000/api/v1/influencers/trending/categories"
```

---

## Notes

1. **Embeddings:** Stored only in Azure AI Search, not in Cosmos DB (saves ~2.4GB storage)
2. **Cache:** Category metadata is cached for faster responses
3. **Search Performance:** Hybrid search combines keyword, vector, and metadata filters
4. **Conversation Context:** Chat search maintains context using conversation_id
5. **Pagination:** Use `limit` and `offset` for pagination
6. **Response Times:** 
   - Basic search: ~100-200ms
   - NLP search: ~300-500ms
   - Chat search: ~400-1500ms (first query slower due to AI analysis)

---

## Support

For issues or questions, check the logs or contact the development team.
