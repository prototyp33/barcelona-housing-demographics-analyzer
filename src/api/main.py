"""FastAPI main application.

Barcelona Housing Analytics REST API serving XGBoost predictions,
neighborhood data, and investment recommendations.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time

from .routers import (
    barrios_router,
    predictions_router,
    investment_router,
    clusters_router,
)
from .models import HealthResponse, ErrorResponse
from .services import get_model_service, get_db_service
from . import __version__

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - startup and shutdown events."""
    # Startup
    logger.info("Starting Barcelona Housing Analytics API...")
    
    # Initialize services
    model_service = get_model_service()
    db_service = get_db_service()
    
    logger.info(f"Model loaded: {model_service.model is not None}")
    logger.info(f"Database connected: {db_service.health_check()}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Barcelona Housing Analytics API...")


# Create FastAPI app
app = FastAPI(
    title="Barcelona Housing Analytics API",
    description="REST API for Barcelona housing market predictions and analytics",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing."""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response


# Include routers
app.include_router(barrios_router)
app.include_router(predictions_router)
app.include_router(investment_router)
app.include_router(clusters_router)


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint.
    
    Returns:
        Health status with service availability
    """
    model_service = get_model_service()
    db_service = get_db_service()
    
    return HealthResponse(
        status="healthy",
        version=__version__,
        database_connected=db_service.health_check(),
        model_loaded=model_service.model is not None
    )


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information.
    
    Returns:
        API welcome message and links
    """
    return {
        "message": "Barcelona Housing Analytics API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "barrios": "/barrios",
            "predictions": "/predictions",
            "investment": "/investment/recommend",
            "clusters": "/clusters"
        }
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions.
    
    Args:
        request: The request that caused the exception
        exc: The exception that was raised
        
    Returns:
        JSON error response
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    error_response = ErrorResponse(
        error="Internal Server Error",
        detail=str(exc)
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode='json')
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
