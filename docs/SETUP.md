# Setup Guide - AI Influencer Discovery System

This guide outlines everything you need to create and configure to get the system running.

## Prerequisites

- Python 3.9 or higher
- Azure account with active subscription
- Local MongoDB instance (for data migration)

## 1. Azure Resources to Create

### 1.1 Azure Cosmos DB (NoSQL API)

**Steps:**

1. Go to Azure Portal → Create Resource
2. Search for "Azure Cosmos DB"
3. Select "Azure Cosmos DB for NoSQL"
4. Configure:
   - **Subscription**: Your subscription
   - **Resource Group**: Create new or use existing
   - **Account Name**: `influencer-discovery-cosmos` (or your choice)
   - **Location**: Choose closest region
   - **Capacity mode**: Provisioned throughput (start with 400 RU/s)
   - **API**: Core (SQL)
5. Click "Review + Create" → "Create"

**After Creation:**

1. Go to your Cosmos DB account
2. Click "Data Explorer"
3. Create Database:
   - Database ID: `influencer_db`
4. Create Container:
   - Container ID: `influencers`
   - Partition key: `/platform`
   - Throughput: 400 RU/s (can scale later)

**Get Connection Details:**

1. Go to "Keys" in left menu
2. Copy:
   - URI (Endpoint)
   - Primary Key

### 1.2 Azure AI Search

**Steps:**

1. Go to Azure Portal → Create Resource
2. Search for "Azure AI Search"
3. Configure:
   - **Subscription**: Your subscription
   - **Resource Group**: Same as Cosmos DB
   - **Service Name**: `influencer-search-2` (or your choice)
   - **Location**: Same region as Cosmos DB
   - **Pricing Tier**: Basic (for development) or Standard (for production)
4. Click "Review + Create" → "Create"

**After Creation:**

1. Go to your Search service
2. Get Admin Key:
   - Go to "Keys" in left menu
   - Copy "Primary admin key"
3. Note the Search service URL (shown on Overview page)

* **Create Search Index:**
  You'll need to create the index programmatically or via Azure Portal. The index schema is defined in the code. You can use the Azure Portal or create a script to set it up.

Index Name: `influencers-index`

Required Fields:

- `id` (Edm.String, key)
- `influencer_id` (Edm.Int64)
- `name` (Edm.String, searchable)
- `username` (Edm.String, filterable)
- `platform` (Edm.String, filterable)
- `city` (Edm.String, filterable)
- `creator_type` (Edm.String, filterable)
- `followers_count` (Edm.Int64, filterable, sortable)
- `engagement_rate_value` (Edm.Double, filterable, sortable)
- `interest_categories` (Collection(Edm.String), filterable)
- `primary_category` (Edm.String, filterable)
- `embedding` (Collection(Edm.Single), vector field, 768 dimensions)

### 1.3 Azure OpenAI

**Steps:**

* Go to Azure Portal → Create Resource
* Search for "Azure OpenAI"
* Configure:
  - **Subscription**: Your subscription
  - **Resource Group**: Same as above
  - **Region**: Choose available region
  - **Name**: `influencer-openai` (or your choice)
  - **Pricing Tier**: Choose based on needs
* Click "Review + Create" → "Create"

**After Creation:**

1. Go to your OpenAI resource
2. Click "Go to Azure OpenAI Studio"
3. Deploy Models:
   - **Embedding Model**: `text-embedding-3-large`
     - Deployment name: `text-embedding-3-large`
   - **Chat Model**: `gpt-4o` or `gpt-4`
     - Deployment name: `gpt-4o`
4. Get Keys:
   - Go to "Keys and Endpoint" in Azure Portal
   - Copy:
     - Endpoint
     - Key 1

## 2. Local MongoDB Setup (For Migration)

If you already have MongoDB running locally, skip this step.

1. Install MongoDB Community Edition
2. Start MongoDB service
3. Note connection string: `mongodb://localhost:27017`

## 3. Environment Configuration

### 3.1 Create `.env` File

Create a `.env` file in the project root:

```env
# Application Settings
DEBUG=False
ENVIRONMENT=development

# CORS Origins (comma-separated)
CORS_ORIGINS=*

# Azure Cosmos DB
AZURE_COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
AZURE_COSMOS_KEY=your-primary-key-here
AZURE_COSMOS_DATABASE=influencer_db
AZURE_COSMOS_CONTAINER=influencers

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://influencer-search.search.windows.net
AZURE_SEARCH_KEY=your-search-admin-key-here
AZURE_SEARCH_INDEX_NAME=influencers-index

# Azure AI Foundry (or Azure OpenAI)
AZURE_OPENAI_ENDPOINT=https://influencer-ai-foundry.openai.azure.com/
AZURE_OPENAI_API_KEY=your-ai-foundry-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=text-embedding-3-large
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o

# OpenAI (Optional - fallback)
OPENAI_API_KEY=

# Local MongoDB (for migration)
LOCAL_MONGODB_URI=mongodb://localhost:27017
LOCAL_MONGODB_DATABASE=your-database-name
LOCAL_MONGODB_COLLECTION=your-collection-name

# Search Configuration
SEARCH_BATCH_SIZE=100
EMBEDDING_BATCH_SIZE=100
MIGRATION_BATCH_SIZE=1000
RRF_WEIGHT_KEYWORD=0.4
RRF_WEIGHT_VECTOR=0.6

# AI Agent Configuration
NLP_AGENT_TEMPERATURE=0.3
NLP_AGENT_MAX_TOKENS=1000
```

### 3.2 Replace Placeholder Values

Replace all placeholder values in `.env` with your actual Azure resource details.

## 4. Python Environment Setup

### 4.1 Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 5. Data Migration

### 5.1 Prepare Your Data

Ensure your local MongoDB has the influencer data in the expected format (matching the JSON schema).

### 5.2 Run Migration

```bash
python scripts/migrate_to_cosmos.py
```

This will:

- Connect to local MongoDB
- Read all influencer records
- Normalize and validate data
- Migrate to Azure Cosmos DB
- Show progress and statistics

## 6. Generate Embeddings

Generate embeddings for all influencers:

```bash
python scripts/generate_embeddings.py
```

This script will:
- Read all influencers from Cosmos DB
- Generate embeddings using Azure OpenAI
- Update records in Cosmos DB with embeddings
- Upsert documents to Azure AI Search with embeddings

**Note:** This can take time for large datasets (200K records). The script processes in batches and shows progress.

## 7. Create Azure AI Search Index

Create the search index programmatically:

```bash
python scripts/create_search_index.py
```

This script will:
- Create the `influencers-index` with all required fields
- Configure vector search with HNSW algorithm
- Handle existing index (asks if you want to recreate)

**Alternative: Using Azure Portal**
1. Go to your Azure AI Search service
2. Click "Import data" or "Add index"
3. Manually create index with the schema defined above

## 8. Complete Setup (Automated)

**Option 1: Run Complete Setup Script**

Run all setup steps in one go:

```bash
python scripts/setup_complete.py
```

This orchestrates:
1. Configuration validation
2. Azure AI Search index creation
3. Data migration (optional)
4. Embedding generation (optional)
5. Final validation

**Option 2: Run Steps Individually**

If you prefer to run steps separately:

1. Create index: `python scripts/create_search_index.py`
2. Migrate data: `python scripts/migrate_to_cosmos.py`
3. Generate embeddings: `python scripts/generate_embeddings.py`
4. Validate: `python scripts/check_setup.py`

## 9. Validate Setup

Before starting the API, validate your setup:

```bash
python scripts/check_setup.py
```

This script will check:

- ✓ Azure Cosmos DB connection and database/container
- ✓ Azure AI Search connection and index
- ✓ Azure OpenAI connection and model deployments (embedding + chat)
- ✓ Local MongoDB connection (for migration)
- ✓ Service classes initialization

Fix any errors before proceeding.

## 10. Start the API

```bash
uvicorn main:app --reload
```

The API will be available at:

- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 11. Verify Setup

### 11.1 Test Health Endpoint

```bash
curl http://localhost:8000/health
```

### 11.2 Test Categories Endpoint

```bash
curl http://localhost:8000/api/v1/influencers/categories
```

### 11.3 Test NLP Search

```bash
curl -X POST http://localhost:8000/api/v1/influencers/search/nlp \
  -H "Content-Type: application/json" \
  -d '{"query": "Find me a fitness micro-influencer in Mumbai", "limit": 10}'
```

## 12. Cost Optimization Tips

1. **Cosmos DB**: Start with 400 RU/s, scale up as needed
2. **Azure AI Search**: Use Basic tier for development
3. **Azure AI Foundry**: Monitor token usage, use appropriate models
4. **Caching**: Implement Redis caching for frequently accessed data
5. **Batch Operations**: Use batch processing for embeddings to reduce API calls

## Troubleshooting

### Common Issues

1. **Connection Errors**: Verify all endpoints and keys in `.env`
2. **Index Not Found**: Ensure Azure AI Search index is created
3. **Embedding Errors**: Check Azure OpenAI deployment names
4. **Migration Failures**: Check MongoDB connection and data format
5. **Rate Limiting**: Adjust batch sizes in configuration

## Next Steps

- [ ] Create all Azure resources
- [ ] Configure `.env` file
- [ ] Install Python dependencies
- [ ] Run data migration
- [ ] Create Azure AI Search index
- [ ] Generate embeddings
- [ ] Test API endpoints
- [ ] Deploy to production (optional)
