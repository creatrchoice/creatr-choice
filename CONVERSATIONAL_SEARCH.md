# Conversational Search - Chat-like Interface

## 🎯 Overview

The conversational search endpoint allows users to refine their search results through a chat-like interface. Users can start with an initial query and then make follow-up refinements to narrow down results.

## 🔄 How It Works

### Flow Example:

```
1. User: "Find fitness influencers"
   → System returns results + conversation_id

2. User: "Show me only those in Mumbai" (with conversation_id)
   → System merges filters: city=Mumbai + previous filters
   → Returns refined results

3. User: "With more than 100K followers" (with conversation_id)
   → System merges: min_followers=100000 + previous filters
   → Returns further refined results

4. User: "Only micro-influencers" (with conversation_id)
   → System merges: creator_type=micro + max_followers=100000
   → Returns final refined results
```

## 📡 API Endpoint

**POST** `/api/v1/influencers/search/chat`

### Request Body

```json
{
  "query": "Find fitness influencers in Mumbai",
  "conversation_id": "optional-conversation-id",
  "context": {
    "previous_filters": { ... },
    "previous_query": "...",
    "previous_results_count": 25
  },
  "limit": 10,
  "offset": 0
}
```

### Response

```json
{
  "influencers": [ ... ],
  "total": 25,
  "limit": 10,
  "offset": 0,
  "has_more": true,
  "search_time_ms": 245.3,
  "conversation_id": "abc-123-def-456",
  "applied_filters": {
    "city": "Mumbai",
    "interest_categories": ["Fitness"],
    "min_followers": 100000
  },
  "refinement_summary": "Refined search: filtered by city: Mumbai, increased minimum followers to 100,000",
  "suggestions": [
    "Filter by specific city",
    "Show only high engagement influencers",
    "Filter by budget/price range"
  ]
}
```

## 💬 Usage Examples

### Example 1: Initial Search

```bash
curl -X POST "http://localhost:8000/api/v1/influencers/search/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find fitness influencers",
    "limit": 10
  }'
```

**Response includes:**
- `conversation_id`: Save this for follow-up queries
- `applied_filters`: Filters that were applied
- `suggestions`: Suggested next steps

### Example 2: Refinement - Add City Filter

```bash
curl -X POST "http://localhost:8000/api/v1/influencers/search/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me only those in Mumbai",
    "conversation_id": "abc-123-from-previous-response",
    "limit": 10
  }'
```

### Example 3: Refinement - Add Follower Requirement

```bash
curl -X POST "http://localhost:8000/api/v1/influencers/search/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "With more than 100K followers",
    "conversation_id": "abc-123",
    "limit": 10
  }'
```

### Example 4: Refinement - Add Engagement Filter

```bash
curl -X POST "http://localhost:8000/api/v1/influencers/search/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Only high engagement influencers",
    "conversation_id": "abc-123",
    "limit": 10
  }'
```

### Example 5: Refinement - Add Category

```bash
curl -X POST "http://localhost:8000/api/v1/influencers/search/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Add fashion category",
    "conversation_id": "abc-123",
    "limit": 10
  }'
```

### Example 6: Refinement - Budget Filter

```bash
curl -X POST "http://localhost:8000/api/v1/influencers/search/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "More affordable ones",
    "conversation_id": "abc-123",
    "limit": 10
  }'
```

## 🧠 Understanding Refinement Queries

The NLP agent understands various refinement patterns:

### Filter Additions:
- "Show me only those in [city]" → Adds city filter
- "With more than [X] followers" → Adds min_followers
- "Only micro-influencers" → Sets creator_type and max_followers
- "With high engagement" → Adds min_engagement_rate
- "Add [category]" → Adds to interest_categories

### Filter Modifications:
- "More affordable" → Decreases max_ppc
- "Higher engagement" → Increases min_engagement_rate
- "More followers" → Increases min_followers

### Filter Removals:
- "Remove city filter" → Clears city filter
- "Any category" → Clears category filters

## 🔧 How Filter Merging Works

When you make a refinement:

1. **New filters** are extracted from your query
2. **Previous filters** are retrieved from conversation context
3. **Filters are merged**:
   - Text filters (city, platform, category): New values replace old
   - Numeric ranges: More restrictive values are used
   - Lists (categories): Combined and deduplicated
4. **Search is performed** with merged filters
5. **Context is updated** for next refinement

## 📊 Response Features

### 1. **Conversation ID**
- Unique ID for the conversation session
- Use it in subsequent requests to maintain context
- Stored in-memory (for production, use Redis/database)

### 2. **Applied Filters**
- Shows all filters currently applied
- Helps users understand what filters are active

### 3. **Refinement Summary**
- Human-readable summary of what changed
- Example: "Refined search: filtered by city: Mumbai, increased minimum followers to 100,000"

### 4. **Suggestions**
- AI-generated suggestions for next steps
- Based on current filters and result count
- Helps users discover new ways to refine

## 🎨 Frontend Integration Example

```javascript
// Initial search
const response1 = await fetch('/api/v1/influencers/search/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Find fitness influencers',
    limit: 10
  })
});
const data1 = await response1.json();
const conversationId = data1.conversation_id;

// Refinement
const response2 = await fetch('/api/v1/influencers/search/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Show me only those in Mumbai',
    conversation_id: conversationId,
    limit: 10
  })
});
const data2 = await response2.json();
```

## ⚠️ Important Notes

1. **Conversation Storage**: Currently uses in-memory storage. For production:
   - Use Redis for session management
   - Or use a database to persist conversations
   - Or make it stateless (pass full context each time)

2. **Context Management**: 
   - If `conversation_id` is provided, context is retrieved automatically
   - If not provided, a new conversation is started
   - Context expires when server restarts (in-memory storage)

3. **Filter Merging Logic**:
   - Numeric filters use more restrictive values
   - Text filters are replaced
   - List filters are combined

## 🚀 Benefits

- **Natural Interaction**: Users can refine searches naturally
- **Progressive Refinement**: Build complex searches step by step
- **Context Awareness**: System remembers previous filters
- **Smart Suggestions**: AI suggests next refinement steps
- **User-Friendly**: No need to understand complex filter syntax
