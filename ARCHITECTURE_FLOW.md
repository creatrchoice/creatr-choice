# AI Influencer Discovery - System Flow & Architecture

## 🏗️ Overall Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                    (Frontend / API Client)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI APPLICATION                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Endpoints:                                          │  │
│  │  - POST /api/v1/influencers/search/nlp                  │  │
│  │  - POST /api/v1/influencers/search/hybrid                │  │
│  │  - GET  /api/v1/influencers/search                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INFLUENCER SERVICE LAYER                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ NLP Agent    │  │ Embedding    │  │ Hybrid       │        │
│  │ (GPT-4o)     │  │ Service      │  │ Search       │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Azure OpenAI │    │ Azure AI     │    │ Azure Cosmos │
│ (Embeddings) │    │ Search       │    │ DB           │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 🔄 Natural Language Search Flow (NLP Endpoint)

### Step-by-Step Process:

```
1. USER QUERY
   └─> "Find me a fitness micro-influencer in Mumbai who is affordable"
       │
       ▼
2. API ENDPOINT: POST /api/v1/influencers/search/nlp
   └─> Receives: NaturalLanguageSearchRequest
       {
         "query": "Find me a fitness micro-influencer in Mumbai who is affordable",
         "limit": 10,
         "offset": 0
       }
       │
       ▼
3. INFLUENCER SERVICE: search_nlp()
   └─> Step 3a: NLP Agent Analysis
       │
       ├─> NLPAgent.analyze_query()
       │   │
       │   ├─> Get available categories from Cosmos DB
       │   │   └─> CategoryDiscoveryService.get_categories()
       │   │
       │   ├─> Build system prompt with categories
       │   │   └─> get_query_analysis_prompt(categories)
       │   │       Includes:
       │   │       - Available interest categories
       │   │       - Available cities
       │   │       - Creator types
       │   │       - Platforms
       │   │
       │   ├─> Create LangChain chain
       │   │   └─> PromptTemplate | AzureChatOpenAI | JsonOutputParser
       │   │
       │   └─> Call Azure OpenAI (GPT-4o)
       │       └─> Returns: QueryAnalysisResult
       │           {
       │             "search_intent": "Looking for affordable fitness micro-influencers in Mumbai",
       │             "extracted_filters": {
       │               "interest_categories": ["Fitness"],
       │               "city": "Mumbai",
       │               "creator_type": "micro",
       │               "min_followers": null,
       │               "max_followers": 100000,
       │               "max_ppc": 50000
       │             },
       │             "confidence": 0.95
       │           }
       │
       └─> Step 3b: Generate Embedding
           │
           ├─> EmbeddingService.generate_embedding(query)
           │   └─> Calls Azure OpenAI (text-embedding-3-large)
           │       └─> Returns: 3072-dimensional vector
           │
           └─> Step 3c: Hybrid Search
               │
               ├─> Convert extracted filters to SearchFilters
               │   └─> SearchFilters(**analysis.extracted_filters)
               │
               └─> HybridSearchService.search()
                   │
                   ├─> Build OData filter string
                   │   └─> "city eq 'Mumbai' and creator_type eq 'micro' 
                   │        and followers_count le 100000 and ppc le 50000"
                   │
                   ├─> AzureSearchStore.hybrid_search()
                   │   │
                   │   ├─> Keyword Search (BM25)
                   │   │   └─> Query: "fitness micro-influencer Mumbai affordable"
                   │   │
                   │   ├─> Vector Search (Cosine Similarity)
                   │   │   └─> VectorizedQuery with embedding
                   │   │
                   │   └─> Metadata Filters (OData)
                   │       └─> Applied to both keyword and vector results
                   │
                   └─> Azure AI Search combines results using RRF
                       (Reciprocal Rank Fusion)
                       └─> Returns: Ranked results with scores
       │
       ▼
4. RESPONSE: EnhancedSearchResponse
   {
     "influencers": [
       {
         "id": "12345",
         "username": "fitness_mumbai",
         "display_name": "Fitness Mumbai",
         "platform": "instagram",
         "followers": 85000,
         "engagement_rate": 4.5,
         "location": "Mumbai",
         "relevance_score": 0.92
       },
       ...
     ],
     "total": 25,
     "limit": 10,
     "offset": 0,
     "has_more": true,
     "search_time_ms": 245.3
   }
```

## 🔍 Hybrid Search Flow (Direct Endpoint)

### Step-by-Step Process:

```
1. USER REQUEST
   └─> POST /api/v1/influencers/search/hybrid
       {
         "query": "fitness influencer",
         "vector_query": [0.123, 0.456, ...],  // Optional
         "filters": {
           "platform": "instagram",
           "city": "Mumbai",
           "min_followers": 50000,
           "max_followers": 200000,
           "interest_categories": ["Fitness"]
         },
         "limit": 10,
         "offset": 0
       }
       │
       ▼
2. INFLUENCER SERVICE: search_hybrid()
   └─> HybridSearchService.search()
       │
       ├─> Convert filters to dictionary
       ├─> Build OData filter string
       └─> AzureSearchStore.hybrid_search()
           │
           ├─> Keyword Search (if query provided)
           │   └─> BM25 algorithm on text fields
           │
           ├─> Vector Search (if vector_query provided)
           │   └─> Cosine similarity on embedding field
           │
           └─> Apply Metadata Filters
               └─> OData filter expression
       │
       ▼
3. AZURE AI SEARCH
   └─> Performs hybrid search:
       │
       ├─> Keyword Results: Ranked by BM25 score
       ├─> Vector Results: Ranked by cosine similarity
       └─> Combines using RRF (Reciprocal Rank Fusion)
           └─> Formula: RRF(d) = Σ 1/(k + rank_i(d))
           └─> Applies metadata filters to both result sets
       │
       ▼
4. RESULTS
   └─> Ranked influencers with relevance scores
```

## 📊 Data Flow Architecture

### Data Storage & Indexing:

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA PIPELINE                           │
└─────────────────────────────────────────────────────────────┘

1. SOURCE DATA (MongoDB)
   └─> 198,514 influencer records
       │
       ▼
2. MIGRATION
   └─> scripts/migrate_to_cosmos.py
       │
       ├─> Reads from MongoDB
       ├─> Normalizes data
       ├─> Validates records
       └─> Writes to Azure Cosmos DB
           └─> Partition key: platform
       │
       ▼
3. EMBEDDING GENERATION
   └─> scripts/generate_embeddings.py
       │
       ├─> Reads from Cosmos DB
       ├─> Generates embeddings (Azure OpenAI)
       │   └─> Input: name + username + categories
       │   └─> Output: 3072-dimensional vector
       │
       ├─> Updates Cosmos DB
       │   └─> Adds "embedding" field to each document
       │
       └─> Indexes to Azure AI Search
           └─> Creates searchable documents with:
               - Metadata fields (filterable)
               - Embedding field (vector searchable)
               - Text fields (keyword searchable)
```

### Search Index Structure:

```
Azure AI Search Index: "influencers-index"
├─> Fields:
    ├─> id (Key, String)
    ├─> influencer_id (Int64)
    ├─> name (String, Searchable)
    ├─> username (String, Filterable, Sortable)
    ├─> platform (String, Filterable, Facetable)
    ├─> city (String, Filterable, Facetable)
    ├─> creator_type (String, Filterable, Facetable)
    ├─> followers_count (Int64, Filterable, Sortable)
    ├─> engagement_rate_value (Double, Filterable, Sortable)
    ├─> interest_categories (Collection[String], Filterable, Facetable)
    ├─> primary_category (String, Filterable, Facetable)
    └─> embedding (Collection[Single], Vector, 3072 dimensions)
        └─> Vector Search Profile: "my-vector-profile"
            └─> Algorithm: HNSW (Hierarchical Navigable Small World)
```

## 🧠 How Components Work Together

### 1. NLP Agent (Query Understanding)
- **Purpose**: Converts natural language to structured filters
- **Technology**: Azure OpenAI GPT-4o
- **Input**: Free-form text query
- **Output**: Structured filters (categories, location, budget, etc.)
- **Features**:
  - Understands intent ("affordable" → low PPC)
  - Maps to available categories
  - Extracts implicit filters
  - Confidence scoring

### 2. Embedding Service (Semantic Understanding)
- **Purpose**: Converts text to vector embeddings
- **Technology**: Azure OpenAI text-embedding-3-large
- **Input**: Text query or influencer data
- **Output**: 3072-dimensional vector
- **Use Cases**:
  - Semantic similarity search
  - Finding similar influencers
  - Understanding query intent

### 3. Hybrid Search (Multi-Modal Search)
- **Purpose**: Combines multiple search strategies
- **Components**:
  - **Keyword Search (BM25)**: Exact text matching
  - **Vector Search**: Semantic similarity
  - **Metadata Filters**: Structured filtering
- **Ranking**: Reciprocal Rank Fusion (RRF)
- **Benefits**:
  - Finds exact matches (keyword)
  - Finds similar concepts (vector)
  - Applies business rules (filters)

### 4. Category Discovery (Dynamic Metadata)
- **Purpose**: Discovers available filter options
- **Source**: Cosmos DB data
- **Output**: CategoryMetadata with:
  - Available categories
  - City list
  - Creator types
  - Statistics (counts, averages)
- **Use**: Helps NLP agent understand valid options

## 🔄 Complete Request Flow Example

### Example: "Find fitness influencers in Mumbai with high engagement"

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER REQUEST                                             │
│    POST /api/v1/influencers/search/nlp                      │
│    { "query": "Find fitness influencers in Mumbai with      │
│                high engagement", "limit": 10 }              │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. NLP AGENT ANALYSIS                                       │
│    ├─> Gets categories from Cosmos DB                      │
│    ├─> Builds prompt with available options                 │
│    ├─> Calls GPT-4o                                        │
│    └─> Extracts:                                           │
│        - interest_categories: ["Fitness"]                  │
│        - city: "Mumbai"                                    │
│        - min_engagement_rate: 4.0                          │
│        - confidence: 0.92                                  │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. EMBEDDING GENERATION                                     │
│    └─> Converts query to 3072-dim vector                   │
│        [0.123, -0.456, 0.789, ...]                         │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. HYBRID SEARCH                                            │
│    ├─> Keyword: "fitness influencers Mumbai high engagement"│
│    ├─> Vector: Cosine similarity search                    │
│    └─> Filters:                                            │
│        - interest_categories/any(c: c eq 'Fitness')        │
│        - city eq 'Mumbai'                                  │
│        - engagement_rate_value ge 4.0                      │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. AZURE AI SEARCH                                          │
│    ├─> Executes keyword search (BM25)                      │
│    ├─> Executes vector search (HNSW)                        │
│    ├─> Applies filters to both                             │
│    └─> Combines with RRF ranking                           │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. RESULTS                                                  │
│    └─> Returns top 10 influencers with:                    │
│        - Relevance scores                                  │
│        - All metadata fields                               │
│        - Search time                                       │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Key Features

### 1. **Natural Language Understanding**
- Understands free-form queries
- Extracts implicit requirements
- Maps to available data

### 2. **Multi-Modal Search**
- Keyword: Exact text matching
- Vector: Semantic similarity
- Filters: Structured constraints

### 3. **Intelligent Ranking**
- Combines multiple signals
- Relevance scoring
- Business rule application

### 4. **Scalability**
- Handles 200K+ records
- Fast search (< 500ms)
- Efficient indexing

### 5. **Production Ready**
- Error handling
- Logging
- Retry logic
- Timeout management

## 📈 Performance Characteristics

- **NLP Analysis**: ~500-1000ms (GPT-4o call)
- **Embedding Generation**: ~200-500ms (Azure OpenAI)
- **Hybrid Search**: ~100-300ms (Azure AI Search)
- **Total Response Time**: ~800-1800ms

## 🔐 Security & Reliability

- **Azure Authentication**: Key-based
- **Error Handling**: Graceful degradation
- **Rate Limiting**: Built into Azure services
- **Retry Logic**: Automatic retries with backoff
- **Logging**: Comprehensive logging for debugging
