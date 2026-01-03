"""FastAPI main application.

Barcelona Housing Analytics REST API serving XGBoost predictions,
neighborhood data, and investment recommendations.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from contextlib import asynccontextmanager
import logging
import time

from .routers import (
    barrios_router,
    predictions_router,
    investment_router,
    clusters_router,
    stats_router,
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
    {
        "name": "stats",
        "description": "General statistics, KPIs and aggregated data tables for analysis.",
    },
]


# Create FastAPI app with docs disabled to allow for custom themed overrides
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
    docs_url=None,       # Disabled for custom theme
    redoc_url=None,      # Disabled for custom theme
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

# --- THEME CONSTANTS ---
THEME_CSS = """
/* State-of-the-art Premium Mesh Theme for Swagger */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Outfit:wght@600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #030303;
    --primary: #6366f1;
    --primary-glow: rgba(99, 102, 241, 0.2);
    --accent: #a855f7;
    --border: rgba(255, 255, 255, 0.08);
    --card-bg: rgba(255, 255, 255, 0.02);
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
    --get-color: #6366f1;
    --post-color: #10b981;
}

body {
    background-color: var(--bg) !important;
    margin: 0;
}

/* Background Mesh */
.swagger-ui::before {
    content: '';
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: 
        radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(168, 85, 247, 0.1) 0px, transparent 50%),
        radial-gradient(at 50% 100%, rgba(30, 64, 175, 0.08) 0px, transparent 50%);
    z-index: -1;
    pointer-events: none;
}

.swagger-ui {
    color: var(--text-main) !important;
    font-family: 'Inter', sans-serif !important;
}

/* HIGH-END SECTION HEADERS (TAGS) */
.swagger-ui .opblock-tag { 
    background: rgba(255, 255, 255, 0.03) !important;
    backdrop-filter: blur(12px);
    border: 1px solid var(--border) !important;
    border-left: 4px solid var(--primary) !important;
    border-radius: 12px !important;
    padding: 24px 20px !important;
    margin: 40px 0 20px 0 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    color: #fff !important;
    letter-spacing: -0.02em !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3) !important;
}

.swagger-ui .opblock-tag:hover {
    background: rgba(255, 255, 255, 0.05) !important;
    border-color: rgba(99, 102, 241, 0.4) !important;
    transform: translateX(4px);
}

.swagger-ui .opblock-tag small {
    color: var(--text-muted) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 400 !important;
    font-size: 1rem !important;
    display: block;
    margin-top: 8px !important;
}

/* FIXING SCHEMAS SECTION (JSON Schema 2020-12 Renderer) */
.swagger-ui section.models { 
    background: rgba(255, 255, 255, 0.01) !important; 
    border: 1px solid var(--border) !important; 
    border-radius: 24px !important; 
    margin: 60px 20px !important;
    overflow: hidden;
    backdrop-filter: blur(10px);
}

.swagger-ui section.models h4 { 
    color: #fff !important; 
    font-family: 'Outfit' !important; 
    font-size: 2rem !important;
    padding: 30px !important; 
    border-bottom: 1px solid var(--border);
    background: rgba(255,255,255,0.02);
}

/* Target the specific modern Swagger accordion buttons */
.swagger-ui .json-schema-2020-12-accordion,
.swagger-ui .json-schema-2020-12-expand-deep-button {
    background-color: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: #fff !important;
    padding: 8px 16px !important;
    box-shadow: none !important;
}

.swagger-ui .json-schema-2020-12-accordion:hover,
.swagger-ui .json-schema-2020-12-expand-deep-button:hover {
    background-color: rgba(255, 255, 255, 0.08) !important;
}

/* Fix Labels and Titles inside Schemas */
.swagger-ui .json-schema-2020-12__title {
    color: #fff !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
}

.swagger-ui .json-schema-2020-12-property-name {
    color: var(--primary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
}

.swagger-ui .json-schema-2020-12-property-type {
    color: #2dd4bf !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.swagger-ui .json-schema-2020-12-property-required {
    color: #fb7185 !important;
}

/* Brace and punctuation styling */
.swagger-ui .json-schema-2020-12-head {
    color: var(--text-muted) !important;
}

/* Legacy Model Support (just in case) */
.swagger-ui .model-title { 
    color: #fff !important; 
    background: rgba(255,255,255,0.05) !important; 
    padding: 6px 14px !important;
    border-radius: 10px !important;
}

/* Eliminate Harsh Outlines & Headers */
.swagger-ui .opblock:focus-within { outline: none !important; }
.swagger-ui .opblock .opblock-section-header { 
    background: transparent !important; 
    border-bottom: 1px solid var(--border) !important; 
    padding: 12px 20px !important;
}

/* Navigation & Status Styling */
.swagger-ui .info .title { 
    font-size: 4.5rem !important; 
    background: linear-gradient(180deg, #fff 0%, #777 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-family: 'Outfit' !important; 
    letter-spacing: -0.06em !important;
}

.swagger-ui .topbar { background-color: rgba(0,0,0,0.5) !important; backdrop-filter: blur(15px); }
.swagger-ui .scheme-container { background: transparent !important; box-shadow: none !important; }

/* Custom Badge Styling */
.swagger-ui .opblock .opblock-summary-method {
    border-radius: 10px !important;
    font-weight: 800;
    font-family: 'Outfit', sans-serif !important;
}

/* Endpoint Row Adjustments */
.swagger-ui .opblock {
    margin-bottom: 20px !important;
    border-radius: 16px !important;
    background: rgba(255, 255, 255, 0.02) !important;
}
"""

# Re-inject the custom style into the Swagger head
@app.get("/docs", include_in_schema=False)
async def themed_swagger_ui_html():
    html = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - API Docs",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )
    # Injecting our custom theme and fonts into the head
    custom_head = f"""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Outfit:wght@700;800&display=swap" rel="stylesheet">
    <style>{THEME_CSS}</style>
    """
    return HTMLResponse(content=html.body.decode().replace("</head>", f"{custom_head}</head>"))

@app.get("/redoc", include_in_schema=False)
async def themed_redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Reference",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
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
app.include_router(stats_router)


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


# Root endpoint with Premium HTML landing page
@app.get("/", response_class=HTMLResponse, tags=["root"], include_in_schema=False)
async def root():
    """Root endpoint with a premium, state-of-the-art landing page.
    
    Returns:
        HTML page with high-end aesthetic and interactive elements.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BCN Housing Analytics | API Intelligence</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Outfit:wght@400;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #6366f1;
                --primary-glow: rgba(99, 102, 241, 0.4);
                --accent: #a855f7;
                --bg: #030303;
                --card-bg: rgba(255, 255, 255, 0.03);
                --card-border: rgba(255, 255, 255, 0.08);
                --text-main: #f8fafc;
                --text-muted: #94a3b8;
            }

            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: 'Inter', sans-serif;
                background-color: var(--bg);
                color: var(--text-main);
                overflow-x: hidden;
                line-height: 1.6;
            }

            /* Premium Mesh Gradient Background */
            .mesh {
                position: fixed;
                top: 0; left: 0; width: 100%; height: 100%;
                background: 
                    radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
                    radial-gradient(at 100% 0%, rgba(168, 85, 247, 0.15) 0px, transparent 50%),
                    radial-gradient(at 50% 100%, rgba(30, 64, 175, 0.1) 0px, transparent 50%);
                z-index: -1;
            }

            .container {
                max-width: 1100px;
                margin: 0 auto;
                padding: 80px 24px;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }

            /* Hero Section */
            .hero {
                text-align: center;
                margin-bottom: 80px;
                animation: fadeInDown 0.8s ease-out;
            }

            .badge {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid var(--card-border);
                padding: 6px 16px;
                border-radius: 99px;
                font-size: 0.85rem;
                font-weight: 500;
                color: var(--primary);
                margin-bottom: 24px;
                letter-spacing: 0.02em;
            }

            h1 {
                font-family: 'Outfit', sans-serif;
                font-size: clamp(2.5rem, 8vw, 4.5rem);
                font-weight: 800;
                line-height: 1.1;
                letter-spacing: -0.04em;
                margin-bottom: 24px;
                background: linear-gradient(180deg, #fff 0%, #aaa 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }

            .hero p {
                font-size: 1.25rem;
                color: var(--text-muted);
                max-width: 600px;
                margin: 0 auto 40px;
                font-weight: 300;
            }

            /* Stats Grid */
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1px;
                background: var(--card-border);
                border-radius: 24px;
                overflow: hidden;
                border: 1px solid var(--card-border);
                margin-bottom: 60px;
            }

            .stat-card {
                background: #080808;
                padding: 32px;
                text-align: center;
            }

            .stat-value {
                font-family: 'Outfit', sans-serif;
                font-size: 2.5rem;
                font-weight: 700;
                color: #fff;
                margin-bottom: 4px;
            }

            .stat-label {
                font-size: 0.875rem;
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 0.1em;
            }

            /* Feature Cards */
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 24px;
                margin-bottom: 80px;
            }

            .card {
                position: relative;
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                border-radius: 24px;
                padding: 32px;
                transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
                overflow: hidden;
                cursor: pointer;
                text-decoration: none;
                color: inherit;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }

            .card:hover {
                transform: translateY(-8px);
                border-color: rgba(99, 102, 241, 0.4);
                background: rgba(255, 255, 255, 0.05);
                box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            }

            .card::before {
                content: '';
                position: absolute;
                top: 0; left: 0; width: 100%; height: 100%;
                background: radial-gradient(circle at top right, rgba(99, 102, 241, 0.1), transparent 70%);
                opacity: 0; transition: opacity 0.4s;
            }

            .card:hover::before { opacity: 1; }

            .card-icon {
                font-size: 2rem;
                margin-bottom: 24px;
                display: block;
            }

            .card h3 {
                font-family: 'Outfit', sans-serif;
                font-size: 1.5rem;
                margin-bottom: 12px;
                color: #fff;
            }

            .card p {
                color: var(--text-muted);
                font-size: 0.95rem;
                margin-bottom: 24px;
            }

            .card-action {
                font-weight: 600;
                font-size: 0.875rem;
                color: var(--primary);
                display: flex;
                align-items: center;
                gap: 8px;
            }

            /* Final Footer */
            .footer {
                text-align: center;
                padding: 40px 0;
                border-top: 1px solid var(--card-border);
            }

            .footer-copy {
                font-size: 0.875rem;
                color: var(--text-muted);
            }

            @keyframes fadeInDown {
                from { opacity: 0; transform: translateY(-20px); }
                to { opacity: 1; transform: translateY(0); }
            }

            /* Responsive tweaks */
            @media (max-width: 768px) {
                h1 { font-size: 3rem; }
                .container { padding: 40px 20px; }
            }
        </style>
    </head>
    <body>
        <div class="mesh"></div>
        
        <div class="container">
            <header class="hero">
                <div class="badge">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #10b981; display: inline-block;"></span>
                    API SYSTEM ONLINE • v""" + __version__ + """
                </div>
                <h1>BCN Housing Intelligence</h1>
                <p>High-fidelity data engine for Barcelona's real estate market. Powered by XGBoost and deep demographic insights.</p>
                
                <div style="display: flex; gap: 16px; justify-content: center;">
                    <a href="/docs" style="background: var(--primary); color: white; padding: 14px 32px; border-radius: 12px; text-decoration: none; font-weight: 600; box-shadow: 0 10px 25px var(--primary-glow); transition: 0.3s; border: 1px solid rgba(255,255,255,0.1);">Launch Swagger</a>
                    <a href="https://github.com/prototyp33/barcelona-housing-demographics-analyzer" style="background: rgba(255,255,255,0.05); color: white; padding: 14px 32px; border-radius: 12px; text-decoration: none; font-weight: 600; border: 1px solid var(--card-border); transition: 0.3s;">View Source</a>
                </div>
            </header>

            <section class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">73</div>
                    <div class="stat-label">Neighborhoods</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">5.8%</div>
                    <div class="stat-label">Avg Yield</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">ML</div>
                    <div class="stat-label">XGBoost Engine</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">+12Y</div>
                    <div class="stat-label">History</div>
                </div>
            </section>

            <div class="grid">
                <a href="/docs" class="card">
                    <div>
                        <span class="card-icon">⚡</span>
                        <h3>Smart Valuations</h3>
                        <p>Real-time neighborhood pricing models with anomaly detection and market deviation metrics.</p>
                    </div>
                    <div class="card-action">EXPLORE ENDPOINTS →</div>
                </a>

                <a href="/docs#/investment" class="card">
                    <div>
                        <span class="card-icon">�</span>
                        <h3>Investment Engine</h3>
                        <p>Algorithmic scouting for high-yield, growth, or safe-haven opportunities across the city.</p>
                    </div>
                    <div class="card-action">CALCULATE ROI →</div>
                </a>

                <a href="/docs#/barrios" class="card">
                    <div>
                        <span class="card-icon">📊</span>
                        <h3>Demographic Deep-Scan</h3>
                        <p>Access precise data on household income, Gini index, and structural building attributes.</p>
                    </div>
                    <div class="card-action">VIEW DATASETS →</div>
                </a>
            </div>

            <footer class="footer">
                <p class="footer-copy">Engineered for accuracy. Powered by Open Data BCN & Cadastre.</p>
            </footer>
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
