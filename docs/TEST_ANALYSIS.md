# Conversational Search Test Analysis

## 📋 Test Scripts Overview

### 1. `test_conversational_search_simple.py` ✅
- **Type**: Unit tests (no API calls)
- **Status**: All tests PASSED (5/5)
- **Purpose**: Tests core logic (filter merging, context management, etc.)
- **Speed**: Fast (~1 second)
- **Dependencies**: None (no server required)

### 2. `test_conversational_search_api.py` ✅
- **Type**: API integration tests (HTTP requests)
- **Status**: Ready to run
- **Purpose**: Tests actual API endpoint with real HTTP requests
- **Speed**: Fast (30s timeout per request)
- **Dependencies**: Requires server running (`uvicorn main:app --reload`)

### 3. `test_conversational_search.py` ⚠️
- **Type**: Full integration tests (direct service calls)
- **Status**: Slow (makes direct Azure service calls)
- **Purpose**: Tests complete flow with database
- **Speed**: Very slow (can take minutes)
- **Dependencies**: Requires all Azure services configured

## 🎯 Recommended Testing Approach

**Use `test_conversational_search_api.py`** - It's the best balance:
- ✅ Tests actual API endpoint (real HTTP requests)
- ✅ Fast (30s timeout per request)
- ✅ Tests the complete user flow
- ✅ Easy to debug (HTTP status codes, responses)

## 📊 Test Flow Analysis

### Conversation Flow (as tested in API script):

```
1. [USER] "Find fitness influencers"
   ↓
   [SYSTEM] Returns results + conversation_id
   - Extracts: interest_categories=["Fitness"]
   - Returns: List of fitness influencers
   - Generates: conversation_id (e.g., "abc-123")

2. [USER] "Show me only those in Mumbai"
   ↓
   [SYSTEM] Refines search with city filter
   - Merges: city="Mumbai" + previous filters
   - Returns: Filtered results
   - Summary: "Refined search: filtered by city: Mumbai"

3. [USER] "With more than 100K followers"
   ↓
   [SYSTEM] Adds follower requirement
   - Merges: min_followers=100000 + previous filters
   - Returns: Further refined results
   - Summary: "increased minimum followers to 100,000"

4. [USER] "Only high engagement influencers"
   ↓
   [SYSTEM] Adds engagement filter
   - Merges: min_engagement_rate=4.0 + previous filters
   - Returns: Final refined results
   - Summary: "added engagement filter"
```

## 🔍 Expected Test Results

### Test 1: Initial Search
- **Query**: "Find fitness influencers"
- **Expected Response**:
  - Status: 200 OK
  - Total results: > 0
  - Conversation ID: Generated UUID
  - Applied filters: `interest_categories: ["Fitness"]`
  - Suggestions: 2-3 suggestions

### Test 2: Refinement - Add City
- **Query**: "Show me only those in Mumbai"
- **Expected Response**:
  - Status: 200 OK
  - Total results: < previous (filtered)
  - Applied filters: `city: "Mumbai"` + previous filters
  - Refinement summary: "filtered by city: Mumbai"

### Test 3: Refinement - Add Follower Filter
- **Query**: "With more than 100K followers"
- **Expected Response**:
  - Status: 200 OK
  - Applied filters: `min_followers: 100000` + previous filters
  - Refinement summary: "increased minimum followers to 100,000"

### Test 4: Refinement - Add Engagement Filter
- **Query**: "Only high engagement influencers"
- **Expected Response**:
  - Status: 200 OK
  - Applied filters: `min_engagement_rate: 4.0` + previous filters
  - Refinement summary: "added engagement filter"

## 🚀 How to Run the API Test

### Step 1: Start the Server
```bash
cd /Users/pankajrajput/Documents/code/personal/secrate/ai-influener-discovery
source venv/bin/activate
uvicorn main:app --reload
```

### Step 2: Run the Test (in another terminal)
```bash
cd /Users/pankajrajput/Documents/code/personal/secrate/ai-influener-discovery
source venv/bin/activate
python scripts/test_conversational_search_api.py
```

## 📈 Performance Expectations

- **Initial Search**: 500-2000ms (includes NLP analysis + search)
- **Refinement Queries**: 300-1500ms (faster, uses cached context)
- **Total Test Time**: ~5-10 seconds for all 4 tests

## 🔧 Troubleshooting

### Issue: "Could not connect to http://localhost:8000"
**Solution**: Start the server first:
```bash
uvicorn main:app --reload
```

### Issue: Tests timeout
**Solution**: 
- Check if Azure services are configured
- Verify `.env` file has correct credentials
- Check network connectivity

### Issue: No results returned
**Solution**:
- Verify data is migrated to Cosmos DB
- Check if embeddings are generated
- Verify Azure AI Search index exists

## 📝 Test Output Format

The test script provides:
1. **Message Flow**: Shows user messages and system responses
2. **Response Details**: Total results, filters, suggestions
3. **Filter Evolution**: How filters change through conversation
4. **Performance Metrics**: Search time for each query
5. **Test Summary**: Pass/fail status for each test

## ✅ Success Criteria

All tests pass if:
- ✅ Server responds with 200 OK
- ✅ Conversation ID is generated and maintained
- ✅ Filters are correctly applied and merged
- ✅ Results are filtered correctly
- ✅ Refinement summaries are generated
- ✅ Suggestions are provided

## 🎉 Expected Final Output

```
================================================================================
TEST SUMMARY
================================================================================

📊 Results: 4/4 tests passed

📋 Test Details:
   ✅ Initial Search
   ✅ Refinement - Add City
   ✅ Refinement - Add Follower Filter
   ✅ Refinement - Add Engagement Filter

================================================================================
CONVERSATION FLOW ANALYSIS
================================================================================

💬 Messages Sent:
   1. User: 'Find fitness influencers'
   2. User: 'Show me only those in Mumbai'
   3. User: 'With more than 100K followers'
   4. User: 'Only high engagement influencers'

🔄 Conversation ID: abc-123-def-456

✅ All tests PASSED!
🎉 Conversational search API is working correctly!
```
