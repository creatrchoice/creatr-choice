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
    description="API for discovering and analyzing influencers using AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
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
