# Average Views Integration - Changes Summary

## ✅ Changes Made

### 1. **Response Models Updated**
   - **`app/models/influencer.py`**: Added `average_views: Optional[int]` to `Influencer` model
   - This field will now be returned in all search responses

### 2. **Filter Models Updated**
   - **`app/models/search.py`**: Added `min_avg_views` and `max_avg_views` to `SearchFilters`
   - **`app/models/query_analysis.py`**: Added `min_avg_views` and `max_avg_views` to `ExtractedFilters`
   - NLP agent can now extract view-based filters from queries

### 3. **Search Service Updated**
   - **`app/services/hybrid_search.py`**:
     - Added `avg_views_count` to filter dictionary
     - Added `average_views` to response conversion (extracts from `avg_views_count`)

### 4. **Azure Search Store Updated**
   - **`app/db/azure_search_store.py`**: Added OData filter generation for avg_views:
     - `min_avg_views` → `avg_views_count ge {value}`
     - `max_avg_views` → `avg_views_count le {value}`

### 5. **Search Index Updated**
   - **`scripts/create_search_index.py`**: Added `avg_views_count` field to search index
   - Field type: `Int64`, filterable and sortable

### 6. **Embedding Generation Updated**
   - **`scripts/generate_embeddings.py`**: Added `avg_views_count` to search documents

### 7. **NLP Prompt Updated**
   - **`app/prompts/query_analysis_prompt.py`**: Added view-based query understanding:
     - "high views" or "viral content" → `avg_views_count > 100000`
     - "low views" → `avg_views_count < 10000`
     - "1M views" → `avg_views_count >= 1000000`

## 🔄 Next Steps Required

### 1. **Recreate Search Index** (IMPORTANT!)
The existing search index doesn't have the `avg_views_count` field. You need to recreate it:

```bash
python scripts/create_search_index.py
# Answer "yes" when asked to delete and recreate
```

### 2. **Regenerate Embeddings** (Optional but Recommended)
After recreating the index, you may want to regenerate embeddings to include avg_views_count in search documents:

```bash
# This will update existing documents with avg_views_count
# Or wait for the current embedding generation to complete
```

## 📝 Usage Examples

### Natural Language Query
```bash
curl -X POST "http://localhost:8000/api/v1/influencers/search/nlp" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find influencers with high views and good engagement",
    "limit": 10
  }'
```

The NLP agent will extract:
- `min_avg_views: 100000` (from "high views")
- `min_engagement_rate: 4.0` (from "good engagement")

### Direct Hybrid Search
```bash
curl -X POST "http://localhost:8000/api/v1/influencers/search/hybrid" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "fitness influencers",
    "filters": {
      "min_avg_views": 50000,
      "max_avg_views": 500000,
      "interest_categories": ["Fitness"]
    },
    "limit": 10
  }'
```

### Response Format
All search responses will now include `average_views`:

```json
{
  "influencers": [
    {
      "id": "12345",
      "username": "fitness_guru",
      "display_name": "Fitness Guru",
      "platform": "instagram",
      "followers": 150000,
      "average_views": 125000,
      "engagement_rate": 4.5,
      "relevance_score": 0.92
    }
  ]
}
```

## 🎯 Filter Examples

The NLP agent understands these view-related queries:
- "high views" → `min_avg_views: 100000`
- "viral content" → `min_avg_views: 100000`
- "low views" → `max_avg_views: 10000`
- "1M views" → `min_avg_views: 1000000`
- "between 50K and 500K views" → `min_avg_views: 50000, max_avg_views: 500000`

## ✅ Verification

All changes have been made and verified:
- ✅ Models updated
- ✅ Services updated
- ✅ Search index script updated
- ✅ Embedding generation script updated
- ✅ NLP prompt updated
- ✅ No linter errors

**Remember to recreate the search index before using avg_views filtering!**
