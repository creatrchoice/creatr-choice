"""
FastAPI application for AI-powered influencer discovery.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()

app = FastAPI(
    title="AI Influencer Discovery API",
    description="""
    ## AI-Powered Influencer Discovery Platform

    A comprehensive API for discovering, analyzing, and managing influencers using advanced AI techniques.

    ### Features

    * 🔍 **Multiple Search Methods**
        - Basic search with filters
        - Natural language search (NLP)
        - Hybrid search (keyword + vector + filters)
        - Conversational search with refinement

    * 📊 **Rich Influencer Data**
        - Profile information
        - Engagement metrics
        - Audience demographics
        - Content analysis
        - Collaboration pricing

    * 🎯 **Smart Filtering**
        - Platform filtering (Instagram, Twitter, YouTube, TikTok, LinkedIn)
        - Category/niche filtering
        - Location-based search
        - Follower count ranges
        - Engagement rate filtering
        - Creator type classification

    * 💬 **Conversational Interface**
        - Chat-like search refinement
        - Context-aware filtering
        - Natural language queries

    ### Getting Started

    1. Use `/api/v1/influencers/categories` to discover available filters
    2. Start with basic search: `/api/v1/influencers/?query=fitness&platform=instagram`
    3. Try natural language search: `/api/v1/influencers/search/nlp`
    4. Use conversational search for iterative refinement: `/api/v1/influencers/search/chat`

    ### Authentication

    Currently, the API does not require authentication. This may change in future versions.

    ### Rate Limits

    Rate limits may apply. Please contact support for enterprise access.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.example.com",
            "description": "Production server"
        }
    ],
)

# CORS middleware
origins = settings.CORS_ORIGINS
if settings.CORS_ALLOW_CREDENTIALS and origins == ["*"]:
    origins = []
    import logging
    logging.warning("CORS: allow_credentials=True but CORS_ORIGINS is '*'. Set specific origins to fix CORS.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    import asyncio
    from app.services.category_discovery import CategoryDiscoveryService

    # Pre-populate category cache in background (non-blocking)
    async def preload_categories():
        try:
            category_service = CategoryDiscoveryService()
            await asyncio.wait_for(
                category_service.get_categories(),
                timeout=30.0  # 30 seconds to build cache
            )
            print("✅ Category cache preloaded successfully")
        except Exception as e:
            print(f"⚠️  Category cache preload failed (will load on first request): {e}")

    # Start preloading in background
    asyncio.create_task(preload_categories())


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Influencer Discovery API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
