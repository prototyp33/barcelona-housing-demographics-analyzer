"""FastAPI main application.

Barcelona Housing Analytics REST API serving XGBoost predictions,
neighborhood data, and investment recommendations.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
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


# API metadata
tags_metadata = [
    {
        "name": "health",
        "description": "Health check and system status endpoints",
    },
    {
        "name": "barrios",
        "description": "Operations with neighborhoods (barrios). Get detailed information about Barcelona's 73 neighborhoods.",
    },
    {
        "name": "predictions",
        "description": "XGBoost ML model predictions for housing prices. Get fair value estimates and deviation analysis.",
    },
    {
        "name": "investment",
        "description": "Investment recommendations based on budget and strategy. Find the best opportunities in Barcelona.",
    },
    {
        "name": "clusters",
        "description": "Neighborhood segmentation and cluster analysis. Understand market segments.",
    },
]


# Create FastAPI app
app = FastAPI(
    title="Barcelona Housing Analytics API",
    description="""
    🏘️ **Barcelona Housing Market Intelligence API**
    
    A production-ready REST API serving XGBoost-powered predictions and analytics 
    for Barcelona's housing market. Built with FastAPI, this API provides:
    
    * 🎯 **ML Predictions**: XGBoost model trained on 73 neighborhoods
    * 💰 **Investment Recommendations**: Personalized suggestions based on budget and strategy
    * 📊 **Market Analytics**: Comprehensive neighborhood data and segmentation
    * 🗺️ **Geospatial Data**: GeoJSON geometries for all neighborhoods
    
    ## Features
    
    - **Real-time Predictions**: Get fair value estimates with deviation analysis
    - **Investment Strategies**: Yield-focused, safe, or growth-oriented recommendations
    - **Cluster Analysis**: K-Means segmentation of neighborhoods
    - **Historical Data**: Price evolution from 2012-2025
    
    ## Data Sources
    
    - Open Data BCN
    - Portal de Dades (Generalitat de Catalunya)
    - IDESCAT
    - Cadastral data
    
    ## Quick Start
    
    1. Check API health: `GET /health`
    2. Explore neighborhoods: `GET /barrios`
    3. Get predictions: `GET /predictions/{barrio_id}`
    4. Find investments: `POST /investment/recommend`
    
    ---
    
    **Built with ❤️ using FastAPI, XGBoost, and Python**
    """,
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    contact={
        "name": "Barcelona Housing Analytics",
        "url": "https://github.com/prototyp33/barcelona-housing-demographics-analyzer",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
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


# Root endpoint with HTML landing page
@app.get("/", response_class=HTMLResponse, tags=["root"], include_in_schema=False)
async def root():
    """Root endpoint with HTML landing page.
    
    Returns:
        HTML page with API information and links
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Barcelona Housing Analytics API</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 800px;
                width: 100%;
                padding: 40px;
            }
            h1 {
                color: #667eea;
                font-size: 2.5em;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 15px;
            }
            .subtitle {
                color: #666;
                font-size: 1.1em;
                margin-bottom: 30px;
            }
            .badge {
                display: inline-block;
                background: #10b981;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.9em;
                font-weight: 600;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .stat {
                text-align: center;
                padding: 20px;
                background: #f8fafc;
                border-radius: 10px;
            }
            .stat-value {
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
            }
            .stat-label {
                color: #666;
                font-size: 0.9em;
                margin-top: 5px;
            }
            .links {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 30px;
            }
            .link-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-decoration: none;
                transition: transform 0.2s, box-shadow 0.2s;
                display: block;
            }
            .link-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
            }
            .link-title {
                font-size: 1.2em;
                font-weight: 600;
                margin-bottom: 5px;
            }
            .link-desc {
                font-size: 0.9em;
                opacity: 0.9;
            }
            .features {
                margin: 30px 0;
                padding: 20px;
                background: #f8fafc;
                border-radius: 10px;
            }
            .feature {
                margin: 10px 0;
                padding-left: 25px;
                position: relative;
            }
            .feature:before {
                content: "✓";
                position: absolute;
                left: 0;
                color: #10b981;
                font-weight: bold;
            }
            .footer {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
                text-align: center;
                color: #666;
                font-size: 0.9em;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>
                🏘️ Barcelona Housing Analytics
            </h1>
            <div class="subtitle">
                Production-ready REST API for housing market intelligence
                <span class="badge">v""" + __version__ + """</span>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">73</div>
                    <div class="stat-label">Neighborhoods</div>
                </div>
                <div class="stat">
                    <div class="stat-value">XGBoost</div>
                    <div class="stat-label">ML Model</div>
                </div>
                <div class="stat">
                    <div class="stat-value">2012-2025</div>
                    <div class="stat-label">Data Range</div>
                </div>
                <div class="stat">
                    <div class="stat-value">8</div>
                    <div class="stat-label">Endpoints</div>
                </div>
            </div>
            
            <div class="features">
                <h3 style="margin-bottom: 15px; color: #667eea;">🎯 Features</h3>
                <div class="feature">Real-time price predictions with XGBoost ML model</div>
                <div class="feature">Investment recommendations (yield, safe, growth strategies)</div>
                <div class="feature">Neighborhood segmentation with K-Means clustering</div>
                <div class="feature">Historical data from 2012-2025</div>
                <div class="feature">GeoJSON geometries for all neighborhoods</div>
            </div>
            
            <div class="links">
                <a href="/docs" class="link-card">
                    <div class="link-title">📚 Interactive Docs</div>
                    <div class="link-desc">Swagger UI with live testing</div>
                </a>
                <a href="/redoc" class="link-card">
                    <div class="link-title">📖 API Reference</div>
                    <div class="link-desc">ReDoc documentation</div>
                </a>
                <a href="/health" class="link-card">
                    <div class="link-title">💚 Health Check</div>
                    <div class="link-desc">System status</div>
                </a>
                <a href="https://github.com/prototyp33/barcelona-housing-demographics-analyzer" class="link-card" target="_blank">
                    <div class="link-title">🔗 GitHub</div>
                    <div class="link-desc">Source code</div>
                </a>
            </div>
            
            <div class="footer">
                Built with ❤️ using FastAPI, XGBoost, and Python<br>
                <a href="https://github.com/prototyp33/barcelona-housing-demographics-analyzer" style="color: #667eea; text-decoration: none;">
                    View on GitHub →
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


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
